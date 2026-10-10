"""Wrong-product experiment: ask whether the target holds a clearly different KIND of produce (base model, no adapter).

Our labels have 10 wrong products in 348 observations, mostly category swaps (bananas in a citrus area, onions in a
potato area, kiwi packs where orange nets belong). Flagging pays +3 for a catch and costs 3 for a false alarm, so a
flag is worth it only above 50% precision. Writes P(A same / B different / C can't tell) per sample and image mode.
"""
import argparse
import json
import time
from pathlib import Path

PROMPT = ("The planogram assigns this target area to {english} (store label: {product}). Look only at the produce inside "
          "the target. A: it is {english}, or it could be. B: it is clearly a different kind of fruit or vegetable, for "
          "example bananas, onions or kiwi packs where {english} belongs. C: the target is empty, hidden or impossible to "
          "judge. Variety, brand, origin, pack size and printed labels do not make it different. Answer B only when you "
          "are sure. Answer exactly A, B or C.")
MODES = {"context": ("context", "crop", "mask"), "crop": ("crop", "mask")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--ids", type=Path, required=True, help="JSON list of sample ids to ask")
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    import torch
    from PIL import Image
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from ml.infer_sample import ENGLISH

    wanted = set(json.loads(args.ids.read_text()))
    samples = [s for s in json.loads(args.manifest.read_text()) if s["sample_id"] in wanted]
    proc = AutoProcessor.from_pretrained(args.model)
    model = AutoModelForImageTextToText.from_pretrained(args.model, dtype=torch.bfloat16, device_map="cuda").eval()
    letters = [proc.tokenizer.encode(c, add_special_tokens=False)[0] for c in "ABC"]
    out, started = {}, time.perf_counter()
    for n, sample in enumerate(samples, 1):
        product = sample["product_name"]
        text = PROMPT.format(english=ENGLISH.get(product, product), product=product)
        out[sample["sample_id"]] = {}
        for mode, keys in MODES.items():
            images = [Image.open(args.manifest.parent / sample[k]).convert("RGB") for k in keys]
            if mode == "context":
                images[0].thumbnail((640, 640))
            intro = ("First image: store camera, target outlined in red. Second image: rectified target crop. Third image: "
                     if mode == "context" else "First image: rectified target crop. Second image: ")
            prompt = intro + "validity mask; black means outside the camera view, ignore it. " + text
            messages = [{"role": "user", "content": [*[{"type": "image"} for _ in images], {"type": "text", "text": prompt}]}]
            chat = proc.apply_chat_template(messages, add_generation_prompt=True, enable_thinking=False)
            inputs = proc(text=[chat], images=images, return_tensors="pt").to("cuda")
            with torch.inference_mode():
                p = model(**inputs).logits[0, -1].float()[letters].softmax(0).tolist()
            out[sample["sample_id"]][mode] = dict(zip("ABC", p))
        if n % 25 == 0:
            print(f"{n}/{len(samples)} {time.perf_counter() - started:.0f}s", flush=True)
    args.output.write_text(json.dumps(out, indent=1) + "\n")
    print(f"done {len(out)} in {time.perf_counter() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
