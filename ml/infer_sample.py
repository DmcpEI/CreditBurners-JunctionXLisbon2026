"""Cached diagnostic VLM run; scores are uncalibrated, not submission labels."""
import argparse
import hashlib
import json
import time
from pathlib import Path


QUESTIONS = {
    "visibility": "Is the target shelf interior sufficiently visible to inspect? A: yes, including a visibly empty tray. B: no, a lowered/closed curtain, shutter or other obstruction hides the interior. C: insufficient evidence. A raised/open curtain or a narrow shelf edge does not block inspection when the tray interior is visible. Ignore out-of-image padding identified by the mask.",
    "presence": "Is any produce visible inside the target area? A: yes, even one item or a small group at the edge inside the target counts. B: no produce at all; the visible tray is empty. C: cannot determine. Ignore produce outside the target.",
    "stock": "Produce is visible in the target. How stocked is that target display? A: partly stocked, substantial space remains. B: full or nearly full. C: cannot determine. Judge only real visible tray pixels, not masked padding or adjacent trays.",
    "compliance": "Does the visible produce match the expected product {product}? A: matches the product type. B: a different product type is visible. C: no visible produce or insufficient evidence. Printed labels alone are not evidence of the actual product. Do not infer brand or origin from appearance.",
}


def answer_tokens(tokenizer):
    groups = [sorted({ids[0] for text in (code, " " + code)
                      if len(ids := tokenizer.encode(text, add_special_tokens=False)) == 1})
              for code in "ABC"]
    if any(not group for group in groups) or len(set(sum(groups, []))) != sum(map(len, groups)):
        raise ValueError("Answer codes need distinct single-token encodings")
    return groups


def inspect_stages(ask):
    """Stop before asking questions the image cannot support."""
    answers = {}

    def choice(name):
        answers[name] = ask(name)
        value = answers[name]["choice"]
        if value not in "ABC" or len(value) != 1:
            raise ValueError("Invalid answer code")
        return value

    visibility = choice("visibility")
    if visibility != "A":
        return dict(answers=answers, visibility="occluded" if visibility == "B" else "unknown",
                    observed_stock=None, observed_compliance=None, action="inspect")
    presence = choice("presence")
    if presence != "A":
        return dict(answers=answers, visibility="clear", observed_stock="empty" if presence == "B" else None,
                    observed_compliance=None, action="restock" if presence == "B" else "inspect")
    stock = {"A": "half", "B": "full", "C": None}[choice("stock")]
    compliance = {"A": True, "B": False, "C": None}[choice("compliance")]
    action = ("inspect" if stock is None or compliance is None else
              "check_product" if not compliance else "check_stock" if stock == "half" else "ok")
    return dict(answers=answers, visibility="clear", observed_stock=stock,
                observed_compliance=compliance, action=action)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--crop-presence-only", action="store_true",
                        help="Diagnostic ablation: presence only, using crop and mask without camera context")
    args = parser.parse_args()
    image_keys = ("crop", "mask") if args.crop_presence_only else ("context", "crop", "mask")
    samples = json.loads(args.manifest.read_text())
    if len({s["sample_id"] for s in samples}) != len(samples):
        raise ValueError("Duplicate sample IDs")
    cache = json.loads(args.output.read_text()) if args.output.exists() else {}
    pending = []
    for sample in samples:
        digest = hashlib.sha256(Path(__file__).read_bytes() + args.model.encode() + str(args.crop_presence_only).encode()
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
    tokens = answer_tokens(proc.tokenizer)
    model = AutoModelForImageTextToText.from_pretrained(
        args.model, local_files_only=True, dtype=torch.bfloat16, device_map="cuda").eval()
    torch.cuda.synchronize()
    load_seconds = time.perf_counter() - started
    print(f"Loaded in {load_seconds:.1f}s", flush=True)
    for sample, fingerprint in pending:
        started = time.perf_counter()
        images = [Image.open(args.manifest.parent / sample[key]).convert("RGB")
                  for key in image_keys]
        result = dict(sample=sample, fingerprint=fingerprint, model=args.model,
                      load_seconds=load_seconds, scores_uncalibrated=True,
                      input_mode="crop_mask_presence_only" if args.crop_presence_only else "staged_context_crop_mask", answers={})
        def ask(name):
            question = QUESTIONS[name]
            description = ("First image: rectified target crop. Second image: " if args.crop_presence_only else
                           "First image: store camera, target outlined in red. Second image: rectified target crop. Third image: ")
            prompt = (description + "validity mask aligned with the crop; white means real camera pixels, black means outside the camera view. "
                      "Ignore those invalid pixels in the crop; they are neither stock nor a physical obstruction. "
                      + question.format(product=sample["product_name"])
                      + " Answer exactly A, B or C.")
            messages = [{"role": "user", "content": [
                *[{"type": "image"} for _ in images], {"type": "text", "text": prompt}]}]
            text = proc.apply_chat_template(messages, add_generation_prompt=True, enable_thinking=False)
            inputs = proc(text=[text], images=images, return_tensors="pt").to("cuda")
            with torch.inference_mode():
                logits = model(**inputs).logits[0, -1].float()
                scores = torch.stack([torch.logsumexp(logits[group], 0) for group in tokens])
                probabilities = scores.softmax(0).tolist()
                mass = (torch.logsumexp(scores, 0) - torch.logsumexp(logits, 0)).exp().item()
            return dict(scores=dict(zip("ABC", probabilities)),
                                           choice="ABC"[max(range(3), key=probabilities.__getitem__)],
                                           allowed_token_mass=mass)
        if args.crop_presence_only:
            result["answers"]["presence"] = ask("presence")
        else:
            result.update(inspect_stages(ask))
        torch.cuda.synchronize()
        result["seconds"] = time.perf_counter() - started
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
