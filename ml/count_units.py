"""Unit counting for stock (experiment, mentor's idea, 11 October 2026; branch feat/unit-counting).

Idea: count the sellable units on a shelf area (packs, bags, bunches or loose items) and decide the stock level from
the count with thresholds per product: about one unit left = empty (the organiser's "one purchase"), then a fraction
of the area's capacity for half/full. The base Qwen3.8-27B counts from the rectified crop + mask; we read the number
it writes. Capacity per area is estimated from the day's images (`ml/count_rule.py`).
"""
import argparse
import json
import re
import time
from pathlib import Path

PROMPT = ("First image: rectified crop of one supermarket shelf area. Second image: validity mask; black means outside "
          "the camera view, ignore it. The planogram product here is {product} ({english}). Count the sellable units "
          "inside the area: each pack, box, bag, net or bunch counts as one unit; for loose produce count the individual "
          "items (estimate if there are many). Answer with a single whole number only; 0 if the area is empty.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="sample.json (crop, mask, product_name per area)")
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ids", type=Path, help="Optional JSON list of sample ids (default: all)")
    args = parser.parse_args()

    import torch
    from PIL import Image
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from ml.infer_sample import ENGLISH

    samples = json.loads(args.manifest.read_text())
    if args.ids:
        wanted = set(json.loads(args.ids.read_text()))
        samples = [s for s in samples if s["sample_id"] in wanted]
    done = json.loads(args.output.read_text()) if args.output.exists() else {}
    proc = AutoProcessor.from_pretrained(args.model)
    model = AutoModelForImageTextToText.from_pretrained(args.model, dtype=torch.bfloat16, device_map="cuda").eval()
    started = time.perf_counter()
    for n, sample in enumerate(samples, 1):
        if sample["sample_id"] in done:
            continue
        images = [Image.open(args.manifest.parent / sample[k]).convert("RGB") for k in ("crop", "mask")]
        text = PROMPT.format(product=sample["product_name"], english=ENGLISH.get(sample["product_name"], sample["product_name"]))
        messages = [{"role": "user", "content": [{"type": "image"}, {"type": "image"}, {"type": "text", "text": text}]}]
        chat = proc.apply_chat_template(messages, add_generation_prompt=True, enable_thinking=False)
        inputs = proc(text=[chat], images=images, return_tensors="pt").to("cuda")
        with torch.inference_mode():
            out = model.generate(**inputs, max_new_tokens=6, do_sample=False)
        raw = proc.tokenizer.decode(out[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        number = re.search(r"\d+", raw)
        done[sample["sample_id"]] = dict(count=int(number.group()) if number else None, raw=raw)
        if n % 50 == 0:
            args.output.write_text(json.dumps(done) + "\n")
            print(f"{n}/{len(samples)} {time.perf_counter() - started:.0f}s", flush=True)
    args.output.write_text(json.dumps(done) + "\n")
    print(f"COUNT_DONE {len(done)} in {time.perf_counter() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
