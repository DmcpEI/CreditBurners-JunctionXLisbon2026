"""Stock probe: small logistic model on the frozen model's answer-position hidden state + answer log-scores.

Fitted on our labels (no fine-tuning of the VLM). Decision per shelf: empty if P(empty) >= 0.5, else half if
P(half) >= the shelf's threshold, else the likelier of full/empty; the production empty check is applied afterwards.
Random 5-fold (unseen timestamps): 179 vs 163 stock points for per-shelf thresholds on the raw answer; area-grouped
(unseen shelves): 106 vs 101 (342 labels, 10 Oct).
"""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
import numpy as np
from ml.compare_runs import groups
from ml.decision_rule import apply_empty_rule
from ml.scoring import LEVELS, PAYOFF

LV = list(LEVELS)
GRID = (0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 1.01)
PCA_DIMS, C = 16, 0.05


def features(record, state):
    scores = record["answers"]["stock"]["scores"]
    return np.concatenate([state, [math.log(max(scores[c], 1e-6)) for c in "ABCD"]])


def decide(p, threshold):
    if p[0] >= 0.5:
        return "empty"
    return "half" if p[1] >= threshold else ("full" if p[2] >= p[0] else "empty")


def probabilities(params, X):
    Z = ((X[:, :-4] - params["mean"]) / params["scale"]) @ params["components"].T
    Z = np.hstack([Z, X[:, -4:]])
    logits = Z @ params["coef"].T + params["intercept"]
    e = np.exp(logits - logits.max(1, keepdims=True))
    P = np.zeros((len(X), 3))
    P[:, params["classes"]] = e / e.sum(1, keepdims=True)
    return P


def fit(hidden_path, results, empty_results, items):
    from sklearn.decomposition import PCA
    from sklearn.linear_model import LogisticRegression
    data = np.load(hidden_path)
    hidden = {i: s[0] for i, s in zip(data["ids"], data["states"])}  # last layer
    lab = [x for x in items if x["label"]["visibility"] == "clear" and x["label"]["stock_level"] and x["id"] in hidden]
    X = np.array([features(results[x["id"]], hidden[x["id"]]) for x in lab])
    y = np.array([LV.index(x["label"]["stock_level"]) for x in lab])
    mean, scale = X[:, :-4].mean(0), X[:, :-4].std(0) + 1e-6
    pca = PCA(PCA_DIMS, random_state=0).fit((X[:, :-4] - mean) / scale)
    Z = np.hstack([pca.transform((X[:, :-4] - mean) / scale), X[:, -4:]])
    clf = LogisticRegression(C=C, max_iter=3000).fit(Z, y)
    params = dict(mean=mean, scale=scale, components=pca.components_, coef=clf.coef_, intercept=clf.intercept_, classes=clf.classes_)
    P = probabilities(params, X)
    final = lambda i, t: apply_empty_rule(dict(results[lab[i]["id"]], observed_stock=decide(P[i], t)),
                                         empty_results.get(lab[i]["id"]))["observed_stock"]
    pts = lambda i, t: PAYOFF[LV.index(final(i, t))][y[i]]
    default = max(GRID, key=lambda t: sum(pts(i, t) for i in range(len(lab))))
    by_area, thresholds = defaultdict(list), {}
    for i, x in enumerate(lab):
        by_area[x["area_id"]].append(i)
    for area, ix in sorted(by_area.items()):
        score = {t: sum(pts(i, t) for i in ix) for t in GRID}
        best = max(GRID, key=lambda t: (score[t], t == default))
        if score[best] > score[default]:
            thresholds[area] = best
    return params, dict(default=default, areas=thresholds, labels=len(lab))


def apply(params, thresholds, record, state, area):
    """Replace the stock decision of one record (the empty check is applied later by the caller)."""
    p = probabilities(params, features(record, state)[None])[0]
    stock = decide(p, thresholds["areas"].get(area, thresholds["default"]))
    return {**record, "observed_stock": stock, "probe": [round(float(v), 4) for v in p], "decision_rule": "probe"}


def load(path):
    data = np.load(path)
    return {k: data[k] for k in data.files}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hidden", type=Path, help="Production-path hidden states of the labelled observations (.npz)")
    parser.add_argument("results", type=Path)
    parser.add_argument("--empty-results", type=Path, required=True)
    parser.add_argument("--extra-labels", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, default=Path("ml/probe.npz"))
    args = parser.parse_args()
    items = [x for _, xs in groups() for x in xs] + [x for p in args.extra_labels for x in json.loads(p.read_text())["items"]]
    params, thresholds = fit(args.hidden, json.loads(args.results.read_text()), json.loads(args.empty_results.read_text()), items)
    np.savez_compressed(args.output, **params)
    args.output.with_suffix(".json").write_text(json.dumps(thresholds, indent=2) + "\n")
    print(f"probe fitted on {thresholds['labels']} labels; default half threshold {thresholds['default']}; {len(thresholds['areas'])} per-shelf thresholds")
