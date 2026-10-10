"""LoRA fine-tuning of the stock question on our labels (experiment; runs in the jx-fast env with peft).

Same inputs as production (640 px context, crop, mask, stock prompt v1); the training target is the answer
letter (A empty, B half, C full) at the answer position.
"""
import argparse
import json
import random
import time
from pathlib import Path

LETTER = {"empty": "A", "half": "B", "full": "C"}
TARGETS = r".*language_model.*\.(q_proj|k_proj|v_proj|o_proj|in_proj_qkv|out_proj)$"


def encoder(proc, root):
    """Production inputs for one sample: 640 px context, crop, mask, stock prompt v1 (thinking off)."""
    from PIL import Image
    from ml.infer_sample import question_input

    def encode(sample):
        keys, prompt = question_input("stock", sample["product_name"], stock_prompt="v1")
        images = [Image.open(root / sample[k]).convert("RGB") for k in keys]
        images[0].thumbnail((640, 640))  # context, as in production --context-max-side 640
        messages = [{"role": "user", "content": [*[{"type": "image"} for _ in images], {"type": "text", "text": prompt}]}]
        text = proc.apply_chat_template(messages, add_generation_prompt=True, enable_thinking=False)
        return proc(text=[text], images=images, return_tensors="pt").to("cuda")
    return encode


def train(model, proc, encode, samples, labels, epochs, lr, accumulate, seed=0):
    """CE on the answer letter at the last position; model already wrapped with LoRA."""
    import torch
    letter_id = {k: proc.tokenizer.encode(v, add_special_tokens=False)[0] for k, v in LETTER.items()}
    optimiser = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=lr, weight_decay=0.0)
    model.train()
    samples, started = list(samples), time.perf_counter()
    for epoch in range(epochs):
        random.Random(seed + epoch).shuffle(samples)
        total = 0.0
        for n, sample in enumerate(samples, 1):
            logits = model(**encode(sample)).logits[0, -1].float()
            target = torch.tensor(letter_id[labels[sample["sample_id"]]], device="cuda")
            loss = torch.nn.functional.cross_entropy(logits[None], target[None]) / accumulate
            loss.backward()
            total += loss.item() * accumulate
            if n % accumulate == 0 or n == len(samples):
                optimiser.step()
                optimiser.zero_grad()
            if n % 50 == 0:
                print(f"epoch {epoch + 1} {n}/{len(samples)} mean loss {total / n:.3f} {time.perf_counter() - started:.0f}s", flush=True)
        print(f"epoch {epoch + 1} done, mean loss {total / len(samples):.3f}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--labels", type=Path, required=True, help="JSON {sample_id: empty|half|full}")
    parser.add_argument("--train-ids", type=Path, required=True, help="JSON list of sample ids to train on")
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--rank", type=int, default=8)
    parser.add_argument("--accumulate", type=int, default=8)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")

    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForImageTextToText, AutoProcessor

    labels = json.loads(args.labels.read_text())
    train_ids = set(json.loads(args.train_ids.read_text()))
    samples = [s for s in json.loads(args.manifest.read_text()) if s["sample_id"] in train_ids and s["sample_id"] in labels]
    proc = AutoProcessor.from_pretrained(args.model)
    model = AutoModelForImageTextToText.from_pretrained(args.model, dtype=torch.bfloat16, device_map="cuda")
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    model = get_peft_model(model, LoraConfig(r=args.rank, lora_alpha=2 * args.rank, lora_dropout=0.05, target_modules=TARGETS))
    model.print_trainable_parameters()
    started = time.perf_counter()
    train(model, proc, encoder(proc, args.manifest.parent), samples, labels, args.epochs, args.lr, args.accumulate)
    model.save_pretrained(args.output)
    print(f"saved adapter to {args.output} after {time.perf_counter() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
