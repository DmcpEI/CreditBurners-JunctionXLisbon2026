"""Label-tuned stock rule: predict half when a stock answer exists and its B score >= HALF_THRESHOLD.

v1 (0.15) was chosen on 15 development areas and did not transfer to new areas. v2 (0.20) was chosen on
160 development observations from 63 areas (raw and area-weighted points), stock-only answers, 10 Oct.
Not a calibrated probability. Every other decision and fallback is left unchanged.
"""
import argparse
import json
from pathlib import Path

HALF_THRESHOLD = 0.20


def apply_half_rule(record, threshold=HALF_THRESHOLD):
    stock = record.get("answers", {}).get("stock")
    if stock is None or stock["scores"]["B"] < threshold:
        return record
    compliance = record.get("observed_compliance")
    action = "inspect" if compliance is None else "check_product" if not compliance else "check_stock"
    return {**record, "observed_stock": "half", "action": action,
            "decision_rule": f"half_if_stock_B>={threshold}", "stock_before_rule": record.get("observed_stock")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists; preserve prior experiment")
    results = json.loads(args.results.read_text())
    adjusted = {key: apply_half_rule(record) for key, record in results.items()}
    args.output.write_text(json.dumps(adjusted, indent=2) + "\n")
    changed = sum(adjusted[k]["observed_stock"] != results[k]["observed_stock"] for k in results)
    print(f"Applied half_if_stock_B>={HALF_THRESHOLD}: {changed}/{len(results)} stock decisions changed")


if __name__ == "__main__":
    main()
