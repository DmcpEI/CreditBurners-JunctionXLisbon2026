"""Cached diagnostic VLM run; scores are uncalibrated, not submission labels."""
import argparse
import hashlib
import json
import time
from pathlib import Path


QUESTIONS = {
    "visibility": "Is the target shelf interior sufficiently visible to inspect? A: yes, including a visibly empty tray. B: no, a lowered/closed curtain, shutter or other obstruction hides the interior. C: insufficient evidence. A raised/open curtain or a narrow shelf edge does not block inspection when the tray interior is visible. Ignore out-of-image padding identified by the mask.",
    "presence": "Is any produce visible inside the target area? A: yes, even one item or a small group at the edge inside the target counts. B: no produce at all; the visible tray is empty. C: cannot determine. Ignore produce outside the target.",
    "stock": "Judge stock ONLY inside the supplied target polygon, relative to the capacity for the visible product type. Ignore shelf space outside the polygon and adjacent trays. A: empty or nearly depleted relative to capacity. B: half, an intermediate amount. C: full or nearly full. D: insufficient evidence. Large fruit fills capacity with fewer items: two large melons in a target that fits roughly six can be half, whereas two lemons in a target that fits many can be empty. These are examples, not universal count thresholds. Visible produce can still be nearly depleted. Ignore black invalid padding; do not equate surface coverage alone with pile volume.",
    "compliance": "Does the visible produce match the expected product {product}? A: matches the product type. B: a different product type is visible. C: no visible produce or insufficient evidence. Printed labels alone are not evidence of the actual product. Do not infer brand or origin from appearance.",
}
# v2: dev error review showed half->full when many items remain but bare container floor or empty cells are visible.
STOCK_PROMPTS = {
    "v1": QUESTIONS["stock"],
    # v3: organiser guidance (10 Oct): empty = customers would not buy what is left; half = staff would take the time
    # to replenish now; full = not worth replenishing yet; in doubt, choose the lower level.
    "v3": "Judge stock ONLY inside the supplied target polygon. Ignore shelf space outside the polygon and adjacent trays. Think like the store. A: empty: a customer would not be willing to buy what is left (nothing, or only a few leftover items). B: half: products are still sellable, but a staff member would take the time to replenish this shelf now. C: full: well stocked; a staff member would not bother replenishing it yet. D: insufficient evidence. If you are unsure between two levels, choose the lower one. Ignore black invalid padding.",
    # v4: team refinement of the organiser definition: about one purchase left (single pack/bag/bunch) = empty.
    "v4": "Judge stock ONLY inside the supplied target polygon. Ignore shelf space outside the polygon and adjacent trays. Think like the store manager. A: empty: nothing left, or only about one purchase left (a single package, bag or bunch, or a couple of loose items); staff must replenish urgently. B: half: more than one purchase left, but a staff member would take the time to replenish this shelf now. C: full: well stocked; a staff member would not bother replenishing it yet. D: insufficient evidence. If you are unsure between two levels, choose the lower one. Ignore black invalid padding.",
    "v2": "Judge stock ONLY inside the supplied target polygon, relative to the capacity for the visible product type. Ignore shelf space outside the polygon and adjacent trays. Look at how much of the container floor inside the target is covered by produce. A: empty or nearly depleted: only a few items remain relative to capacity and most of the floor is bare. B: half: produce is clearly present, but a noticeable part of the floor is bare, or empty cells, cups or gaps where more items would fit are visible (roughly a quarter or more of the target). Many items can still be half. C: full: produce covers essentially the whole target floor, with little or no bare floor or empty cells visible. D: insufficient evidence. Large fruit fills capacity with fewer items: two large melons in a target that fits roughly six can be half, whereas two lemons in a target that fits many can be empty. These are examples, not universal count thresholds. Ignore black invalid padding.",
}


def answer_tokens(tokenizer, codes="ABC"):
    groups = [sorted({ids[0] for text in (code, " " + code)
                      if len(ids := tokenizer.encode(text, add_special_tokens=False)) == 1})
              for code in codes]
    if any(not group for group in groups) or len(set(sum(groups, []))) != sum(map(len, groups)):
        raise ValueError("Answer codes need distinct single-token encodings")
    return groups


ALL_QUESTIONS = ("visibility", "presence", "stock", "compliance")


def inspect_stages(ask, questions=ALL_QUESTIONS):
    """Stop before asking questions the image cannot support. Skipped stages assume visible / present / compliant."""
    answers = {}

    def choice(name):
        answers[name] = ask(name)
        value = answers[name]["choice"]
        if value not in ("ABCD" if name == "stock" else "ABC") or len(value) != 1:
            raise ValueError("Invalid answer code")
        return value

    visibility = choice("visibility") if "visibility" in questions else "A"
    if visibility != "A":
        return dict(answers=answers, visibility="occluded" if visibility == "B" else "unknown",
                    observed_stock=None, observed_compliance=None, action="inspect")
    presence = choice("presence") if "presence" in questions else "A"
    if presence != "A":
        return dict(answers=answers, visibility="clear", observed_stock="empty" if presence == "B" else None,
                    observed_compliance=True if presence == "B" else None, action="restock" if presence == "B" else "inspect")
    stock = {"A": "empty", "B": "half", "C": "full", "D": None}[choice("stock")]
    compliance = {"A": True, "B": False, "C": None}[choice("compliance")] if "compliance" in questions else True
    action = ("inspect" if stock is None or compliance is None else
              "restock" if stock == "empty" else "check_product" if not compliance else "check_stock" if stock == "half" else "ok")
    return dict(answers=answers, visibility="clear", observed_stock=stock,
                observed_compliance=compliance, action=action)


def question_input(name, product, crop_compliance=True, stock_prompt="v1", stock_crop_only=False):
    crop_only = name == "presence" or (name == "compliance" and crop_compliance) or (name == "stock" and stock_crop_only)
    keys = ("crop", "mask") if crop_only else ("context", "crop", "mask")
    description = ("First image: rectified target crop. Second image: " if crop_only else
                   "First image: store camera, target outlined in red. Second image: rectified target crop. Third image: ")
    question = STOCK_PROMPTS[stock_prompt] if name == "stock" else QUESTIONS[name]
    prompt = (description + "validity mask aligned with the crop; white means real camera pixels, black means outside the camera view. "
              "Ignore those invalid pixels in the crop; they are neither stock nor a physical obstruction. "
              + question.format(product=product) + (" Answer exactly A, B, C or D." if name == "stock" else " Answer exactly A, B or C."))
    return keys, prompt


def question_fingerprint(model, prompt, paths):
    digest = hashlib.sha256((model + "\n" + prompt).encode())
    for path in paths:
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True, type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--crop-presence-only", action="store_true",
                        help="Diagnostic ablation: presence only, using crop and mask without camera context")
    modes.add_argument("--crop-compliance-only", action="store_true",
                       help="Diagnostic ablation: product match using crop and mask only")
    parser.add_argument("--answer-cache", type=Path, help="Reuse identical individual questions across staged runs")
    parser.add_argument("--stock-prompt", choices=sorted(STOCK_PROMPTS), default="v1")
    parser.add_argument("--questions", default=",".join(ALL_QUESTIONS),
                        help="Stages to ask, e.g. presence,stock for guaranteed-visible validation without compliance")
    parser.add_argument("--stock-crop-only", action="store_true", help="Stock question sees crop+mask only, no camera context")
    parser.add_argument("--context-max-side", type=int, default=0,
                        help="Downscale the camera-context image so its longest side is at most this (0 = original)")
    parser.add_argument("--batch-size", type=int, default=1,
                        help="Stock-only runs: answer this many areas per GPU forward pass (left padding)")
    parser.add_argument("--answer-prefix", default="",
                        help='Start the reply with this text (e.g. "Answer: ") for models that explain before answering')
    args = parser.parse_args()
    questions = tuple(q for q in args.questions.split(",") if q)
    if not set(questions) <= set(ALL_QUESTIONS) or "stock" not in questions:
        parser.error("--questions must include stock and only known stages")
    if args.batch_size > 1 and questions != ("stock",):
        parser.error("--batch-size > 1 needs --questions stock (no gated stages)")
    answer_cache = json.loads(args.answer_cache.read_text()) if args.answer_cache and args.answer_cache.exists() else {}
    image_keys = ("crop", "mask") if args.crop_presence_only or args.crop_compliance_only else ("context", "crop", "mask")
    samples = json.loads(args.manifest.read_text())
    if len({s["sample_id"] for s in samples}) != len(samples):
        raise ValueError("Duplicate sample IDs")
    cache = json.loads(args.output.read_text()) if args.output.exists() else {}
    pending = []
    for sample in samples:
        digest = hashlib.sha256(Path(__file__).read_bytes() + args.model.encode() + str((args.crop_presence_only, args.crop_compliance_only, args.stock_prompt, args.answer_prefix)
                                                                                                + (("context", args.context_max_side) if args.context_max_side else ())
                                                                                                + ((questions, args.stock_crop_only) if questions != ALL_QUESTIONS or args.stock_crop_only else ())).encode()
                                + json.dumps(sample, sort_keys=True).encode())
        for key in image_keys:
            digest.update((args.manifest.parent / sample[key]).read_bytes())
        fingerprint = digest.hexdigest()
        previous = cache.get(sample["sample_id"])
        if previous and previous["fingerprint"] != fingerprint:
            raise ValueError("Cached input/settings changed; use a new output file")
        if not previous:
            pending.append((sample, fingerprint))
    if not pending:
        print("All samples cached; no model loaded")
        return

    import torch
    from PIL import Image
    from transformers import AutoProcessor, AutoModelForImageTextToText

    started = time.perf_counter()
    proc = AutoProcessor.from_pretrained(args.model, local_files_only=True)
    tokens = answer_tokens(proc.tokenizer, "ABCD")
    model = AutoModelForImageTextToText.from_pretrained(
        args.model, local_files_only=True, dtype=torch.bfloat16, device_map="cuda").eval()
    torch.cuda.synchronize()
    load_seconds = time.perf_counter() - started
    print(f"Loaded in {load_seconds:.1f}s", flush=True)

    def question_key(prompt):
        # settings that change model input must change the cache key (defaults keep old keys valid)
        return (prompt + ("\n[answer-prefix]" + args.answer_prefix if args.answer_prefix else "")
                + (f"\n[context-max-side]{args.context_max_side}" if args.context_max_side else ""))

    def stock_question(sample):
        keys, prompt = question_input("stock", sample["product_name"], stock_prompt=args.stock_prompt, stock_crop_only=args.stock_crop_only)
        paths = [args.manifest.parent / sample[key] for key in keys]
        return prompt, paths, question_fingerprint(args.model, question_key(prompt), paths)

    def load_images(paths):
        images = [Image.open(path).convert("RGB") for path in paths]
        if args.context_max_side and len(images) == 3:  # context is first when present
            images[0].thumbnail((args.context_max_side, args.context_max_side))
        return images

    def chat_text(prompt, count):
        messages = [{"role": "user", "content": [*[{"type": "image"} for _ in range(count)], {"type": "text", "text": prompt}]}]
        return proc.apply_chat_template(messages, add_generation_prompt=True, enable_thinking=False) + args.answer_prefix

    def answer_from(logits, codes):
        scores = torch.stack([torch.logsumexp(logits[group], 0) for group in tokens[:len(codes)]])
        probabilities = scores.softmax(0).tolist()
        mass = (torch.logsumexp(scores, 0) - torch.logsumexp(logits, 0)).exp().item()
        return dict(scores=dict(zip(codes, probabilities)),
                    choice=codes[max(range(len(codes)), key=probabilities.__getitem__)], allowed_token_mass=mass)

    batched = {}  # question fingerprint -> (answer, seconds share of its batch)
    if args.batch_size > 1:
        proc.tokenizer.padding_side = "left"  # last position = answer position for every row
        todo = {}
        for sample, _ in pending:
            prompt, paths, key = stock_question(sample)
            if key not in answer_cache:
                todo.setdefault(key, (prompt, paths))
        todo = list(todo.items())
        for start in range(0, len(todo), args.batch_size):
            chunk = todo[start:start + args.batch_size]
            began = time.perf_counter()
            texts = [chat_text(prompt, len(paths)) for _, (prompt, paths) in chunk]
            images = [load_images(paths) for _, (_, paths) in chunk]
            inputs = proc(text=texts, images=images, return_tensors="pt", padding=True).to("cuda")
            with torch.inference_mode():
                rows = model(**inputs).logits[:, -1].float()
                answers = [answer_from(row, "ABCD") for row in rows]
            torch.cuda.synchronize()
            share = (time.perf_counter() - began) / len(chunk)
            for (key, _), answer in zip(chunk, answers):
                batched[key] = (answer, share)
            print(f"batch {start // args.batch_size + 1}: {len(chunk)} areas, {share:.3f}s/area", flush=True)

    for sample, fingerprint in pending:
        started = time.perf_counter()
        shares = []
        result = dict(sample=sample, fingerprint=fingerprint, model=args.model, batch_size=args.batch_size, stock_prompt=args.stock_prompt, answer_prefix=args.answer_prefix, questions=questions, stock_crop_only=args.stock_crop_only,
                      load_seconds=load_seconds, scores_uncalibrated=True,
                      input_mode="crop_mask_presence_only" if args.crop_presence_only else "crop_mask_compliance_only" if args.crop_compliance_only else "staged_crop_presence_compliance", answers={})
        def ask(name):
            if name == "stock":
                prompt, paths, fingerprint = stock_question(sample)
            else:
                keys, prompt = question_input(name, sample["product_name"], stock_prompt=args.stock_prompt, stock_crop_only=args.stock_crop_only)
                paths = [args.manifest.parent / sample[key] for key in keys]
                fingerprint = question_fingerprint(args.model, question_key(prompt), paths)
            if fingerprint in answer_cache:
                return {**answer_cache[fingerprint], "cache_hit": True}
            codes = "ABCD" if name == "stock" else "ABC"
            if fingerprint in batched:
                answer, share = batched[fingerprint]
                shares.append(share)
            else:
                images = load_images(paths)
                inputs = proc(text=[chat_text(prompt, len(images))], images=images, return_tensors="pt").to("cuda")
                with torch.inference_mode():
                    answer = answer_from(model(**inputs).logits[0, -1].float(), codes)
            answer_cache[fingerprint] = answer
            if args.answer_cache:
                args.answer_cache.parent.mkdir(parents=True, exist_ok=True)
                temporary = args.answer_cache.with_suffix(".tmp")
                temporary.write_text(json.dumps(answer_cache, indent=2) + "\n")
                temporary.replace(args.answer_cache)
            return {**answer, "cache_hit": False}
        if args.crop_presence_only:
            result["answers"]["presence"] = ask("presence")
        elif args.crop_compliance_only:
            result["answers"]["compliance"] = ask("compliance")
        else:
            result.update(inspect_stages(ask, questions))
        torch.cuda.synchronize()
        result["seconds"] = time.perf_counter() - started + sum(shares)  # batched forward time is shared per area
        result["peak_vram_gb"] = torch.cuda.max_memory_allocated() / 1e9
        cache[sample["sample_id"]] = result
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(".tmp")
        temporary.write_text(json.dumps(cache, indent=2) + "\n")
        temporary.replace(args.output)
        print(sample["sample_id"], {k: v["choice"] for k, v in result["answers"].items()},
              f'{result["seconds"]:.2f}s', flush=True)


if __name__ == "__main__":
    main()
