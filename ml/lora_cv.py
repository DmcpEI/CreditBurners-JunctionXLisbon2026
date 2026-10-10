"""LoRA settings sweep with k-fold cross-validation on all our stock labels (base model loaded once).

Each config trains one adapter per fold on the other folds and writes out-of-fold ABCD scores for every labelled
sample to <output>/<config>.json (resumable per fold). Score with `python -m ml.lora_cv --score <output>`: stock
points with the production empty check, half threshold chosen on the pooled out-of-fold scores (same optimism for
every config). Random folds match the task: validation images are new times of the same shelves.
"""
import argparse
import json
import random
import time
from pathlib import Path

CONFIGS = {  # name: rank, lr, epochs, share of the training folds used
    "r8-lr1e-4-e2": dict(rank=8, lr=1e-4, epochs=2, share=1.0),
    "r8-lr2e-4-e2": dict(rank=8, lr=2e-4, epochs=2, share=1.0),
    "r8-lr1e-4-e3": dict(rank=8, lr=1e-4, epochs=3, share=1.0),
    "r16-lr1e-4-e2": dict(rank=16, lr=1e-4, epochs=2, share=1.0),
    "r8-lr5e-5-e2": dict(rank=8, lr=5e-5, epochs=2, share=1.0),
    "r8-lr1e-4-e1": dict(rank=8, lr=1e-4, epochs=1, share=1.0),
    "r8-lr1e-4-e2-half-data": dict(rank=8, lr=1e-4, epochs=2, share=0.5),
    "r8-lr1e-4-e2-3q-data": dict(rank=8, lr=1e-4, epochs=2, share=0.75),
}


def folds(ids, k, seed=20261011):
    ids = sorted(ids)
    random.Random(seed).shuffle(ids)
    return [ids[i::k] for i in range(k)]


def run(args):
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from ml.finetune import TARGETS, encoder, train
    from ml.infer_sample import answer_tokens

    labels = json.loads(args.labels.read_text())
    samples = {s["sample_id"]: s for s in json.loads(args.manifest.read_text()) if s["sample_id"] in labels}
    split = folds(samples, args.folds)
    proc = AutoProcessor.from_pretrained(args.model)
    model = AutoModelForImageTextToText.from_pretrained(args.model, dtype=torch.bfloat16, device_map="cuda")
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    encode, groups = encoder(proc, args.manifest.parent), answer_tokens(proc.tokenizer, "ABCD")
    args.output.mkdir(parents=True, exist_ok=True)
    for name in args.configs.split(","):
        config, path = CONFIGS[name], args.output / f"{name}.json"
        done = json.loads(path.read_text()) if path.exists() else {}
        for f, test in enumerate(split):
            if all(i in done for i in test):
                continue
            started = time.perf_counter()
            pool = [samples[i] for part in split[:f] + split[f + 1:] for i in part]
            pool = random.Random(f).sample(pool, round(len(pool) * config["share"]))
            peft = get_peft_model(model, LoraConfig(r=config["rank"], lora_alpha=2 * config["rank"], lora_dropout=0.05, target_modules=TARGETS))
            train(peft, proc, encode, pool, labels, config["epochs"], config["lr"], 8, seed=f)
            peft.eval()
            with torch.inference_mode():
                for i in test:
                    logits = peft(**encode(samples[i])).logits[0, -1].float()
                    scores = torch.stack([torch.logsumexp(logits[g], 0) for g in groups]).softmax(0).tolist()
                    done[i] = dict(zip("ABCD", scores))
            model = peft.unload()  # drop this fold's LoRA layers, back to the base model
            torch.cuda.empty_cache()
            path.write_text(json.dumps(done) + "\n")
            print(f"{name} fold {f + 1}/{len(split)}: trained on {len(pool)}, tested {len(test)}, {time.perf_counter() - started:.0f}s", flush=True)
    print("SWEEP_DONE", flush=True)


def score(args):
    from ml.decision_rule import apply_empty_rule, apply_half_rule
    from ml.scoring import LEVELS, PAYOFF
    labels = json.loads(args.labels.read_text())
    empty = json.loads(args.empty_results.read_text())
    order = list(LEVELS)
    grid = [round(0.05 * i, 2) for i in range(1, 20)] + [1.01]
    for path in sorted(args.score.glob("*.json")):
        oof = json.loads(path.read_text())
        def points(threshold):
            total = correct = 0
            for i, scores in oof.items():
                choice = max("ABC", key=scores.get)
                record = dict(answers={"stock": {"scores": scores}}, observed_stock={"A": "empty", "B": "half", "C": "full"}[choice])
                record = apply_empty_rule(apply_half_rule(record, threshold), empty.get(i))
                p, t = order.index(record["observed_stock"]), order.index(labels[i])
                total += PAYOFF[p][t]
                correct += p == t
            return total, correct
        best = max(grid, key=lambda t: points(t)[0])
        (pts, ok), (pts04, _) = points(best), points(0.4)
        print(f"{path.stem:28s} n={len(oof):3d}  points {pts:4d} (half threshold {best}), correct {ok}/{len(oof)};  at 0.4: {pts04}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, nargs="?")
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--model")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--configs", default=",".join(CONFIGS))
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--score", type=Path, help="Score a finished sweep directory instead of running")
    parser.add_argument("--empty-results", type=Path, help="Base-model prompt-v4 results (empty check), for --score")
    args = parser.parse_args()
    score(args) if args.score else run(args)


if __name__ == "__main__":
    main()
