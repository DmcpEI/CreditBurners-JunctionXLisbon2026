"""Cached diagnostic VLM run; scores are uncalibrated, not submission labels."""
import argparse
import hashlib
import json
import time
from pathlib import Path


QUESTIONS = {
    "visibility": "Can you see inside the target produce display? A: clear, including a visibly empty tray. B: hidden by a closed white curtain, shutter, person or other obstruction. C: cannot determine.",
    "stock": "How stocked is the target display? A: empty, no produce visible. B: partly stocked, substantial space remains. C: full or nearly full. Judge the target only, not adjacent trays.",
    "compliance": "Does the visible produce match the expected product {product}? A: matches the product type. B: a different product type is visible. C: no visible produce or insufficient evidence. Printed labels alone are not evidence of the actual product. Do not infer brand or origin from appearance.",
}


def answer_tokens(tokenizer):
    groups = [sorted({ids[0] for text in (code, " " + code)
                      if len(ids := tokenizer.encode(text, add_special_tokens=False)) == 1})
              for code in "ABC"]
    if any(not group for group in groups) or len(set(sum(groups, []))) != sum(map(len, groups)):
        raise ValueError("Answer codes need distinct single-token encodings")
    return groups


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    samples = json.loads(args.manifest.read_text())
    if len({s["sample_id"] for s in samples}) != len(samples):
        raise ValueError("Duplicate sample IDs")
    cache = json.loads(args.output.read_text()) if args.output.exists() else {}
    pending = []
    for sample in samples:
        digest = hashlib.sha256(Path(__file__).read_bytes() + args.model.encode()
                                + json.dumps(sample, sort_keys=True).encode())
        for key in ("context", "crop"):
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
                  for key in ("context", "crop")]
        result = dict(sample=sample, fingerprint=fingerprint, model=args.model,
                      load_seconds=load_seconds, scores_uncalibrated=True, answers={})
        for name, question in QUESTIONS.items():
            prompt = ("First image: store camera, target outlined in red. Second image: rectified target crop. "
                      "Black padding is outside the camera view, not empty shelf. "
                      + question.format(product=sample["product_name"])
                      + " Answer exactly A, B or C.")
            messages = [{"role": "user", "content": [
                {"type": "image"}, {"type": "image"}, {"type": "text", "text": prompt}]}]
            text = proc.apply_chat_template(messages, add_generation_prompt=True, enable_thinking=False)
            inputs = proc(text=[text], images=images, return_tensors="pt").to("cuda")
            with torch.inference_mode():
                logits = model(**inputs).logits[0, -1].float()
                scores = torch.stack([torch.logsumexp(logits[group], 0) for group in tokens])
                probabilities = scores.softmax(0).tolist()
                mass = (torch.logsumexp(scores, 0) - torch.logsumexp(logits, 0)).exp().item()
            result["answers"][name] = dict(scores=dict(zip("ABC", probabilities)),
                                           choice="ABC"[max(range(3), key=probabilities.__getitem__)],
                                           allowed_token_mass=mass)
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
