"""SAM 3 produce coverage per area crop: share of real (valid) crop pixels covered by produce masks. Cached per sample."""
import argparse
import json
import time
from pathlib import Path
from ml.label_set import PACKAGED

PRODUCTS = json.loads(Path(__file__).with_name("products_en.json").read_text())
THRESHOLD = 0.3  # tested Fri: "produce" covers 0.97 at 0.3 vs 0.20 at 0.5


def prompts(product_name):
    names = [PRODUCTS[product_name], "produce"]
    return names + ["bag"] if PACKAGED.search(product_name) else names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--model", default="/workspace/models/sam3")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    samples = json.loads(args.manifest.read_text())
    cache = json.loads(args.output.read_text()) if args.output.exists() else {}
    pending = [s for s in samples if s["sample_id"] not in cache]
    if not pending:
        print("All samples cached")
        return
    import numpy as np
    import torch
    from PIL import Image
    from transformers import Sam3Model, Sam3Processor
    proc = Sam3Processor.from_pretrained(args.model)
    model = Sam3Model.from_pretrained(args.model, dtype=torch.bfloat16).to("cuda").eval()
    for sample in pending:
        started = time.perf_counter()
        image = Image.open(args.manifest.parent / sample["crop"]).convert("RGB")
        valid = np.asarray(Image.open(args.manifest.parent / sample["mask"])) > 0
        union, per_prompt = np.zeros(valid.shape, bool), {}
        for text in prompts(sample["product_name"]):
            inputs = proc(images=image, text=text, return_tensors="pt").to("cuda")
            inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)
            with torch.inference_mode():
                out = model(**inputs)
            masks = proc.post_process_instance_segmentation(out, threshold=THRESHOLD, mask_threshold=0.5,
                                                            target_sizes=inputs["original_sizes"].tolist())[0]["masks"]
            mask = masks.any(0).cpu().numpy() if len(masks) else np.zeros(valid.shape, bool)
            per_prompt[text] = float((mask & valid).sum() / max(valid.sum(), 1))
            union |= mask
        cache[sample["sample_id"]] = dict(coverage=float((union & valid).sum() / max(valid.sum(), 1)),
                                          per_prompt=per_prompt, seconds=time.perf_counter() - started)
        temporary = args.output.with_suffix(".tmp")
        temporary.write_text(json.dumps(cache, indent=2) + "\n")
        temporary.replace(args.output)
    print(f"{len(pending)} crops measured")


if __name__ == "__main__":
    main()
