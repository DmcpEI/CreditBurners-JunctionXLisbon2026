"""Instance counts per shelf crop with SAM 3 (text-prompted detector), for the unit-counting experiment.

For each crop, SAM 3 segments every instance of the product (its English name; "package" too for packed products).
Per crop we keep: number of instances, median instance size (share of the real crop area), and coverage (share of the
real crop covered). Small products (lemons) need more instances to look full than big ones (melons); the adapter in
`ml/count_rule.py --detector` learns that from count, unit size and coverage.
"""
import argparse
import json
import re
import time
from pathlib import Path

PRODUCTS = json.loads(Path(__file__).with_name("products_en.json").read_text())
PACKAGED = re.compile(r'EMB|(?<![/\d])\d+(?:[.,]\d+)?\s*(?:G|GR|KG)\b')
SCORE = 0.3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--model", default="/workspace/models/sam3")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import numpy as np
    import torch
    from PIL import Image
    from transformers import Sam3Model, Sam3Processor
    samples = json.loads(args.manifest.read_text())
    done = json.loads(args.output.read_text()) if args.output.exists() else {}
    proc = Sam3Processor.from_pretrained(args.model)
    model = Sam3Model.from_pretrained(args.model, dtype=torch.bfloat16).to("cuda").eval()
    started = time.perf_counter()
    for n, sample in enumerate(samples, 1):
        if sample["sample_id"] in done:
            continue
        image = Image.open(args.manifest.parent / sample["crop"]).convert("RGB")
        valid = np.asarray(Image.open(args.manifest.parent / sample["mask"]).convert("L")) > 0
        real = max(int(valid.sum()), 1)
        prompts = [PRODUCTS.get(sample["product_name"], "produce")] + (["package"] if PACKAGED.search(sample["product_name"]) else [])
        result = {}
        for text in prompts:
            inputs = proc(images=image, text=text, return_tensors="pt").to("cuda")
            inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)
            with torch.inference_mode():
                out = model(**inputs)
            masks = proc.post_process_instance_segmentation(out, threshold=SCORE, mask_threshold=0.5,
                                                            target_sizes=inputs["original_sizes"].tolist())[0]["masks"]
            masks = [m & valid for m in (masks.cpu().numpy().astype(bool) if len(masks) else [])]
            sizes = sorted(m.sum() / real for m in masks if m.sum() > 0)
            union = np.zeros(valid.shape, bool)
            for m in masks:
                union |= m
            result[text] = dict(count=len(sizes), unit=float(sizes[len(sizes) // 2]) if sizes else 0.0, coverage=float(union.sum() / real))
        done[sample["sample_id"]] = result
        if n % 100 == 0:
            args.output.write_text(json.dumps(done) + "\n")
            print(f"{n}/{len(samples)} {time.perf_counter() - started:.0f}s", flush=True)
    args.output.write_text(json.dumps(done) + "\n")
    print(f"DETECT_DONE {len(done)} in {time.perf_counter() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
