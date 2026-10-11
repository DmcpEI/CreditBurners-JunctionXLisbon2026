"""Detector counts -> empty/half/full with a small learned adapter (unit-counting experiment, branch feat/unit-counting).

  python -m ml.count_adapter data/full-v1/detect-v1.json

Features per crop from SAM 3 instances (`ml/count_detect.py`): log count, median unit size, coverage, and the same
relative to the area's best value over the day (a stand-in for capacity), for the product prompt and, for packed
products, the "package" prompt. Small products have small units, so the adapter can learn that they need more
instances to be half or full. Trained on the training folds only (same 5 folds as the LoRA/YOLO runs); scored alone
and averaged with the submitted hybrid, with the production half rule and empty check.
"""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from ml.decision_rule import apply_empty_rule, apply_half_rule
from ml.infer_sample import ENGLISH
from ml.lora_cv import folds
from ml.scoring import LEVELS, PAYOFF

O = list(LEVELS)
CURTAIN = ("6383_1751001156", "6386_1751001156")
area = lambda i: "_".join(i.split("_")[2:])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("detect", type=Path)
    args = parser.parse_args()
    import numpy as np
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    det = json.loads(args.detect.read_text())
    product = {s["sample_id"]: s["product_name"] for s in json.loads(Path("data/full-v1/sample.json").read_text())}
    main_prompt = lambda i: ENGLISH.get(product[i], "produce")
    get = lambda i, k: det[i].get(k, dict(count=0, unit=0.0, coverage=0.0))
    best = defaultdict(lambda: [1, 1e-3])  # per area: max count, max coverage over the day
    for i in det:
        if not i.startswith(CURTAIN):
            r = get(i, main_prompt(i))
            best[area(i)] = [max(best[area(i)][0], r["count"]), max(best[area(i)][1], r["coverage"])]

    def features(i):
        r, p = get(i, main_prompt(i)), get(i, "package")
        b = best[area(i)]
        return [math.log1p(r["count"]), r["unit"], r["coverage"], r["count"] / max(b[0], 1), r["coverage"] / max(b[1], 1e-3),
                math.log1p(r["count"]) * r["unit"], math.log1p(p["count"]), p["coverage"], float("package" in det[i])]

    labels = json.loads(Path("data/finetune-v1/labels.json").read_text())
    ids = [i for i in labels if i in det]
    Y = json.loads(Path("data/lora-cv/yolo-yolo11n-cls-e15-pad.json").read_text())
    L = json.loads(Path("data/lora-cv/r8-lr2e-4-e2.json").read_text())
    E = {**json.loads(Path("data/full-v1/results-probe-v4.json").read_text()),
         **{k: v for k, v in json.loads(Path("data/full-v1/results-lora2-v4.json").read_text()).items() if v}}

    def decide(i, sc, t=0.4):
        r = apply_half_rule(dict(answers={"stock": {"scores": sc}}, observed_stock={"A": "empty", "B": "half", "C": "full"}[max("ABC", key=sc.get)]), t)
        return apply_empty_rule(r, E.get(i) if L[i]["C"] < 0.5 else None)["observed_stock"]

    models = {"logistic": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000)),
              "boosted trees": lambda: HistGradientBoostingClassifier(max_depth=3, max_iter=150, learning_rate=0.05, random_state=0)}
    adapter = {name: {} for name in models}
    for test in folds(ids, 5):
        train = [i for i in ids if i not in set(test)]
        X = np.array([features(i) for i in train]); y = np.array([O.index(labels[i]) for i in train])
        for name, make in models.items():
            model = make().fit(X, y)
            P = model.predict_proba(np.array([features(i) for i in test]))
            for i, p in zip(test, P):
                full = dict(zip([O[c] for c in model.classes_], p))
                adapter[name][i] = dict(A=full.get("empty", 0.0), B=full.get("half", 0.0), C=full.get("full", 0.0))
    hyb = {i: {k: (Y[i][k] + L[i][k]) / 2 for k in "ABC"} for i in ids}
    print(f"{len(ids)} labelled observations, 5-fold, stock points (max {len(ids)}) at half threshold 0.2 / 0.3 / 0.4 / 0.5")
    rows = [("submitted hybrid (YOLO + LoRA)", hyb)]
    for name in models:
        A = adapter[name]
        rows += [(f"detector adapter ({name}) alone", A),
                 (f"hybrid + adapter ({name}), equal thirds", {i: {k: (Y[i][k] + L[i][k] + A[i][k]) / 3 for k in "ABC"} for i in ids}),
                 (f"hybrid 80% + adapter ({name}) 20%", {i: {k: 0.8 * hyb[i][k] + 0.2 * A[i][k] for k in "ABC"} for i in ids})]
    for name, S in rows:
        res = []
        for t in (0.2, 0.3, 0.4, 0.5):
            p = [decide(i, S[i], t) for i in ids]
            res.append((sum(PAYOFF[O.index(a)][O.index(labels[i])] for a, i in zip(p, ids)), sum(a == labels[i] for a, i in zip(p, ids))))
        print(f"  {name:46s} " + " / ".join(f"{pts} ({ok})" for pts, ok in res))


if __name__ == "__main__":
    main()
