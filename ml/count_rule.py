"""Stock from unit counts (experiment, branch feat/unit-counting): thresholds learned per kind of produce, 5-fold CV.

  python -m ml.count_rule data/full-v1/counts-v1.json

Capacity of an area = its highest count over the day's images (no labels needed). Rule: empty if count <= E,
otherwise half if count / capacity < H, otherwise full. E and H are chosen on the training folds (per kind of produce
when it has enough labels, else global) and scored on the held-out fold, with Sensei's stock points. Also scored:
the submitted hybrid with the count rule as an extra vote (empty override, or count-based half/full override).
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path
from ml.decision_rule import apply_empty_rule, apply_half_rule
from ml.infer_sample import ENGLISH
from ml.lora_cv import folds
from ml.scoring import LEVELS, PAYOFF

O = list(LEVELS)
CURTAIN = ("6383_1751001156", "6386_1751001156")
E_GRID, H_GRID = (0, 1, 2, 3), (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01)


def area(i):
    return "_".join(i.split("_")[2:])


def rule(c, cap, e, h):
    return "empty" if c <= e else "half" if c / max(cap, 1) < h else "full"


def points(pred, truth):
    return PAYOFF[O.index(pred)][O.index(truth)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("counts", type=Path)
    parser.add_argument("--min-labels", type=int, default=15, help="Labels a kind of produce needs for its own thresholds")
    args = parser.parse_args()
    counts = {i: v["count"] for i, v in json.loads(args.counts.read_text()).items() if v["count"] is not None}
    cap = defaultdict(int)
    for i, c in counts.items():
        if not i.startswith(CURTAIN):
            cap[area(i)] = max(cap[area(i)], c)
    labels = json.loads(Path("data/finetune-v1/labels.json").read_text())
    product = {s["sample_id"]: s["product_name"] for s in json.loads(Path("data/full-v1/sample.json").read_text())}
    kind = lambda i: ENGLISH.get(product[i], product[i])
    ids = [i for i in labels if i in counts]
    # submitted hybrid, held out (same folds): padded YOLO + LoRA v2 averaged, half >= 0.4, empty check as in production
    Y = json.loads(Path("data/lora-cv/yolo-yolo11n-cls-e15-pad.json").read_text())
    L = json.loads(Path("data/lora-cv/r8-lr2e-4-e2.json").read_text())
    E = {**json.loads(Path("data/full-v1/results-probe-v4.json").read_text()),
         **{k: v for k, v in json.loads(Path("data/full-v1/results-lora2-v4.json").read_text()).items() if v}}

    def hybrid(i):
        sc = {k: (Y[i][k] + L[i][k]) / 2 for k in "ABC"}
        r = apply_half_rule(dict(answers={"stock": {"scores": sc}}, observed_stock={"A": "empty", "B": "half", "C": "full"}[max("ABC", key=sc.get)]), 0.4)
        return apply_empty_rule(r, E.get(i) if L[i]["C"] < 0.5 else None)["observed_stock"]

    def fit(train, group):
        """Best (E, H) on these labels, per group (kind of produce) with a global fallback."""
        best = lambda rows: max(((e, h) for e in E_GRID for h in H_GRID),
                                key=lambda eh: sum(points(rule(counts[i], cap[area(i)], *eh), labels[i]) for i in rows))
        glob = best(train)
        by = defaultdict(list)
        for i in train:
            by[group(i)].append(i)
        return glob, {g: best(rows) for g, rows in by.items() if len(rows) >= args.min_labels}

    variants = defaultdict(int)
    correct = defaultdict(int)
    for test in folds(ids, 5):
        train = [i for i in ids if i not in set(test)]
        glob, per = fit(train, kind)
        for i in test:
            e, h = per.get(kind(i), glob)
            count_pred = rule(counts[i], cap[area(i)], e, h)
            glob_pred = rule(counts[i], cap[area(i)], *glob)
            hyb = hybrid(i)
            preds = {
                "count rule, global thresholds": glob_pred,
                "count rule, per kind of produce": count_pred,
                "submitted hybrid": hyb,
                "hybrid + count says empty -> empty": "empty" if count_pred == "empty" else hyb,
                "hybrid, but count decides half vs full": hyb if hyb == "empty" else (count_pred if count_pred != "empty" else hyb),
                "majority of hybrid, count rule, YOLO": None,
            }
            yv = {"A": "empty", "B": "half", "C": "full"}[max("ABC", key=Y[i].get)]
            votes = [hyb, count_pred, yv]
            preds["majority of hybrid, count rule, YOLO"] = max(set(votes), key=votes.count) if len(set(votes)) < 3 else hyb
            for name, p in preds.items():
                variants[name] += points(p, labels[i])
                correct[name] += p == labels[i]
    print(f"{len(ids)} labelled observations, 5-fold; capacity = highest count of the area over the day")
    for name in variants:
        print(f"  {name:42s} {variants[name]:4d} points, {correct[name]} correct")


if __name__ == "__main__":
    main()
