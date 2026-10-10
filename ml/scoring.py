"""Sensei's discrete predictions, completeness checks and official payoff rules."""
import argparse
import json
import math
from pathlib import Path

LEVELS = {"empty": 0, "half": 0.5, "full": 1}
PAYOFF = ((1, -2, -2), (-3, 1, -2), (-3, -3, 1))


def flatten(data):
    if not isinstance(data, dict):
        raise ValueError("Submission must be an object")
    result = {}
    for camera, images in data.items():
        if not isinstance(images, dict):
            raise ValueError(f"Invalid camera entry: {camera}")
        for filename, areas in images.items():
            if not isinstance(areas, dict):
                raise ValueError(f"Invalid image entry: {filename}")
            for area, pred in areas.items():
                if not isinstance(pred, dict) or set(pred) != {
                    "planogram_compliant", "stock_level", "stock_value"
                }:
                    raise ValueError(f"Invalid prediction fields: {area}")
                level, value = pred["stock_level"], pred["stock_value"]
                if (type(pred["planogram_compliant"]) is not bool
                        or not isinstance(level, str) or level not in LEVELS
                        or type(value) not in (int, float) or value != LEVELS[level]):
                    raise ValueError(f"Invalid prediction values: {area}")
                result[camera, filename, area] = pred
    return result


def validate_submission(predictions, expected):
    actual = set(flatten(predictions))
    wanted = {tuple(key) for key in expected}
    if actual != wanted:
        raise ValueError(f"Coverage mismatch: {len(wanted-actual)} missing, "
                         f"{len(actual-wanted)} unexpected areas")
    return len(actual)


def choose_stock(probabilities):
    if (len(probabilities) != 3
            or any(not math.isfinite(p) or p < 0 for p in probabilities)
            or not math.isclose(sum(probabilities), 1, abs_tol=1e-6)):
        raise ValueError("Expected three nonnegative probabilities summing to one")
    scores = [sum(a*p for a, p in zip(row, probabilities)) for row in PAYOFF]
    return tuple(LEVELS)[max(range(3), key=lambda i: scores[i])]


def score(truth, predictions):
    truth, predictions = flatten(truth), flatten(predictions)
    counts = dict(areas=len(truth), missing=0, identification_correct=0,
                  identification_wrong=0, stock_correct=0, stock_under=0, stock_over=0)
    total = 0
    for key, target in truth.items():
        if key not in predictions:
            counts["missing"] += 1
            total -= 5
            continue
        pred = predictions[key]
        correct = pred["planogram_compliant"] == target["planogram_compliant"]
        counts["identification_correct" if correct else "identification_wrong"] += 1
        total += 1 if correct else -2
        delta = pred["stock_value"] - target["stock_value"]
        outcome = "stock_correct" if delta == 0 else "stock_under" if delta < 0 else "stock_over"
        counts[outcome] += 1
        total += {"stock_correct": 1, "stock_under": -2, "stock_over": -3}[outcome]
    return {**counts, "score": total, "maximum": 2*len(truth)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score labelled areas; extra predictions are ignored.")
    parser.add_argument("truth", type=Path)
    parser.add_argument("predictions", type=Path)
    args = parser.parse_args()
    print(json.dumps(score(json.loads(args.truth.read_text()),
                           json.loads(args.predictions.read_text())), indent=2))
