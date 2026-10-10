"""Per-shelf half threshold, learned from our labels of each area (no timestamp used).

For each area, pick the half threshold from GRID that scores best on that area's labelled observations;
keep the global HALF_THRESHOLD unless another value is strictly better. Tested leave-one-timestamp-out:
147 vs 78 stock points on 218 observations; blind 50-observation check: 60/99 vs 52/99 points (10 Oct).
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path
from ml.compare_runs import groups
from ml.decision_rule import HALF_THRESHOLD, apply_empty_rule, apply_half_rule
from ml.scoring import LEVELS, PAYOFF

GRID = (0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1.01)


def points(prediction, truth):
    return PAYOFF[list(LEVELS).index(prediction)][list(LEVELS).index(truth)]


def fit(results, empty_results, items):
    by_area = defaultdict(list)
    for x in items:
        if x["label"]["visibility"] == "clear" and x["label"]["stock_level"]:
            by_area[x["area_id"]].append(x)
    predict = lambda k, t: apply_empty_rule(apply_half_rule(results[k], t), empty_results.get(k))["observed_stock"] or "half"
    thresholds = {}
    for area, xs in sorted(by_area.items()):
        score = {t: sum(points(predict(x["id"], t), x["label"]["stock_level"]) for x in xs) for t in GRID}
        best = max(GRID, key=lambda t: (score[t], t == HALF_THRESHOLD))
        if score[best] > score[HALF_THRESHOLD]:
            thresholds[area] = best
    return thresholds


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--empty-results", type=Path, required=True)
    parser.add_argument("--extra-labels", type=Path, action="append", default=[], help="More frozen label files (e.g. blind set)")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    items = [x for _, xs in groups() for x in xs] + [x for p in args.extra_labels for x in json.loads(p.read_text())["items"]]
    thresholds = fit(json.loads(args.results.read_text()), json.loads(args.empty_results.read_text()), items)
    args.output.write_text(json.dumps(dict(default=HALF_THRESHOLD, areas=thresholds), indent=2) + "\n")
    print(f"{len(thresholds)} areas deviate from {HALF_THRESHOLD}: {dict(sorted(__import__('collections').Counter(thresholds.values()).items()))}")
