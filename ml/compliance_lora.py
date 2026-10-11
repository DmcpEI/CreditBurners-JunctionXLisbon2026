"""Wrong-product (planogram compliance) LoRA trained on self-made pairs; experiment, 11 October 2026.

Organiser (Discord, 11 Oct): validation images come from the same cameras; any product that is not the planogram's
product is non-compliant, and teams are expected to train for it. We had only 10 labelled wrong products, so
we make pairs from unlabelled observations: a shelf crop with its own planogram name = A (this product), the same crop
with another area's name = B (different product or variety; half the time the same kind of produce, e.g. Fuji vs
Gala). Crop + mask only, no camera view, so the model must compare what it sees with the name instead of
memorising shelf positions. Evaluated on the labelled observations (never trained on): own name, and a swapped name.
"""
import argparse
import json
import random
import time
from pathlib import Path

PROMPT = ("First image: rectified target crop. Second image: validity mask aligned with the crop; black means outside "
          "the camera view, ignore it. The planogram product for this area is \"{product}\" ({english}). Is that exact "
          "product on this shelf? A: yes, this product. B: no, a different product or variety. C: the area is empty or "
          "it is impossible to tell. Answer exactly A, B or C.")


def pairs(samples, english, seed):
    """Own name -> A; another area's name -> B (half from the same kind of produce when one exists)."""
    rng = random.Random(seed)
    names = sorted({s["product_name"] for s in samples})
    kind = lambda name: english.get(name, name)
    out = []
    for s in samples:
        same = [n for n in names if n != s["product_name"] and kind(n) == kind(s["product_name"])]
        other = [n for n in names if kind(n) != kind(s["product_name"])]
        wrong = rng.choice(same) if same and rng.random() < 0.5 else rng.choice(other)
        out += [({**s, "sample_id": s["sample_id"] + "|own"}, "A"), ({**s, "sample_id": s["sample_id"] + "|swap", "product_name": wrong}, "B")]
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--train-ids", type=Path, help="Unlabelled, visible, not-empty observations to make pairs from")
    parser.add_argument("--eval-ids", type=Path, help="Labelled observations (never trained on)")
    parser.add_argument("--real-labels", type=Path, help="JSON {sample_id: compliant} reviewed observations added to training (own name, x3)")
    parser.add_argument("--adapter-in", type=Path, help="Production: score every sample of the manifest with this adapter (own name only)")
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--rank", type=int, default=16)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    if not args.adapter_in and not (args.train_ids and args.eval_ids):
        parser.error("training needs --train-ids and --eval-ids")

    import torch
    from PIL import Image
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from ml.finetune import TARGETS, train
    from ml.infer_sample import ENGLISH, answer_tokens

    manifest = {s["sample_id"]: s for s in json.loads(args.manifest.read_text())}
    if args.adapter_in:
        return score_manifest(args, manifest)
    train_pairs = pairs([manifest[i] for i in json.loads(args.train_ids.read_text())], ENGLISH, seed=1)
    eval_pairs = pairs([manifest[i] for i in json.loads(args.eval_ids.read_text())], ENGLISH, seed=2)
    if args.real_labels:  # real wrong products (strict review, 11 Oct) next to the made-up swaps
        real = json.loads(args.real_labels.read_text())
        train_pairs += [({**manifest[i], "sample_id": f"{i}|real{k}"}, "A" if ok else "B") for i, ok in real.items() for k in range(3)]
    proc = AutoProcessor.from_pretrained(args.model)
    model = AutoModelForImageTextToText.from_pretrained(args.model, dtype=torch.bfloat16, device_map="cuda")
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    groups = answer_tokens(proc.tokenizer, "ABC")

    def encode(sample):
        images = [Image.open(args.manifest.parent / sample[k]).convert("RGB") for k in ("crop", "mask")]
        text = PROMPT.format(product=sample["product_name"], english=ENGLISH.get(sample["product_name"], sample["product_name"]))
        messages = [{"role": "user", "content": [{"type": "image"}, {"type": "image"}, {"type": "text", "text": text}]}]
        chat = proc.apply_chat_template(messages, add_generation_prompt=True, enable_thinking=False)
        return proc(text=[chat], images=images, return_tensors="pt").to("cuda")

    model = get_peft_model(model, LoraConfig(r=args.rank, lora_alpha=2 * args.rank, lora_dropout=0.05, target_modules=TARGETS))
    started = time.perf_counter()
    print(f"training on {len(train_pairs)} pairs from {len(train_pairs) // 2} observations", flush=True)
    train(model, proc, encode, [s for s, _ in train_pairs], {s["sample_id"]: y for s, y in train_pairs}, args.epochs, args.lr, 8)
    model.save_pretrained(args.output)
    print(f"trained in {time.perf_counter() - started:.0f}s; evaluating {len(eval_pairs)} pairs", flush=True)
    model.eval()
    scores = {}
    with torch.inference_mode():
        for sample, target in eval_pairs:
            logits = model(**encode(sample)).logits[0, -1].float()
            p = torch.stack([torch.logsumexp(logits[g], 0) for g in groups]).softmax(0).tolist()
            scores[sample["sample_id"]] = dict(zip("ABC", p), target=target, product=sample["product_name"])
    (args.output / "eval.json").write_text(json.dumps(scores, indent=1) + "\n")
    print(f"COMPLIANCE_DONE {time.perf_counter() - started:.0f}s", flush=True)


def score_manifest(args, manifest):
    """P(A same / B different / C can't tell) for each sample with its own planogram name -> args.output (JSON)."""
    import torch
    from PIL import Image
    from peft import PeftModel
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from ml.infer_sample import ENGLISH, answer_tokens
    proc = AutoProcessor.from_pretrained(args.model)
    model = AutoModelForImageTextToText.from_pretrained(args.model, dtype=torch.bfloat16, device_map="cuda")
    model = PeftModel.from_pretrained(model, args.adapter_in).eval()
    groups, out, started = answer_tokens(proc.tokenizer, "ABC"), {}, time.perf_counter()
    with torch.inference_mode():
        for sample in manifest.values():
            images = [Image.open(args.manifest.parent / sample[k]).convert("RGB") for k in ("crop", "mask")]
            text = PROMPT.format(product=sample["product_name"], english=ENGLISH.get(sample["product_name"], sample["product_name"]))
            messages = [{"role": "user", "content": [{"type": "image"}, {"type": "image"}, {"type": "text", "text": text}]}]
            chat = proc.apply_chat_template(messages, add_generation_prompt=True, enable_thinking=False)
            logits = model(**proc(text=[chat], images=images, return_tensors="pt").to("cuda")).logits[0, -1].float()
            out[sample["sample_id"]] = dict(zip("ABC", torch.stack([torch.logsumexp(logits[g], 0) for g in groups]).softmax(0).tolist()))
    args.output.write_text(json.dumps(out) + "\n")
    print(f"scored {len(out)} samples in {time.perf_counter() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
