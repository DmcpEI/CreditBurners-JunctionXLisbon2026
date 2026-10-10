"""Full-dataset inputs, then Sensei submission + app snapshots from model results and the locked half rule."""
import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from ml.decision_rule import apply_empty_rule, apply_half_rule, EMPTY_THRESHOLD, HALF_THRESHOLD
from ml.label_set import outlined_context
from ml.prepare import load_planogram, write_json
from ml.scoring import LEVELS, validate_submission

FALLBACK_STOCK, FALLBACK_COMPLIANT = "half", True


def build_inputs(prepared, dataset, output):
    """One infer_sample manifest entry per area observation; crops/masks are referenced, not copied."""
    if output.exists():
        raise ValueError("Output exists; choose a new directory")
    cameras = load_planogram(dataset/"planogram.json")
    (output/"assets").mkdir(parents=True)
    samples = []
    for row in json.loads((prepared/"index.json").read_text()):
        camera, filename, area = row["camera_id"], row["image_file"], row["area_id"]
        key = f"{camera}_{Path(filename).stem}_{area}"
        target = next(a for a in cameras[camera]["products"] if a["area_id"] == area)
        context = f"assets/{key}-context.jpg"
        outlined_context(prepared/"assets"/f"{camera}_{filename}", target["image_coordinates"]).save(output/context, quality=92)
        rel = Path("..")/prepared.name
        samples.append(dict(sample_id=key, camera_id=camera, image_file=filename, area_id=area,
                            product_name=row["product_name"], context=context,
                            crop=str(rel/row["crop_file"]), mask=str(rel/row["valid_mask_file"])))
    write_json(output/"sample.json", samples)
    print(f"{len(samples)} inputs written to {output}")


def reason(record, stock, compliant, fallback, model_mismatch=False, product_checked=True):
    if record is None:
        return "No model result for this area; fixed fallback (half, compliant) used."
    if record.get("visibility") != "clear":
        return f"Model judged the view {record.get('visibility')}; fixed fallback (half, compliant) used. Inspect."
    parts = [f"Model stock: {stock}" + (" (empty check)" if record.get("empty_rule") else " (half rule applied)" if record.get("decision_rule") else "")]
    parts.append("product identity not checked (answered compliant by policy)" if not product_checked else
                 "expected product type visible" if compliant else "a different product type appears visible")
    hint = " Model also flagged a possible wrong product (not used: unreliable on labelled data); check if convenient." if model_mismatch else ""
    return "; ".join(parts) + (". Some fields use the fixed fallback." if fallback else ".") + hint


def build_outputs(prepared, results_path, output, run_id, always_compliant=False, empty_results_path=None, area_thresholds_path=None,
                  probe_path=None, hidden_path=None):
    if output.exists():
        raise ValueError("Output exists; choose a new directory")
    expected = json.loads((prepared/"expected.json").read_text())
    results = json.loads(results_path.read_text())
    empty_results = json.loads(empty_results_path.read_text()) if empty_results_path else None
    area_thresholds = json.loads(area_thresholds_path.read_text()) if area_thresholds_path else dict(default=HALF_THRESHOLD, areas={})
    if probe_path:
        import numpy as np
        from ml import probe
        probe_params, probe_thresholds = probe.load(probe_path), json.loads(probe_path.with_suffix(".json").read_text())
        data = np.load(hidden_path)
        hidden = {i: s[0] for i, s in zip(data["ids"], data["states"])}
    processed = datetime.now(timezone.utc).isoformat()
    submission, snapshots, stats = {}, defaultdict(list), Counter()
    seconds = defaultdict(float)
    for camera, filename, area in expected:
        key = f"{camera}_{Path(filename).stem}_{area}"
        record = results.get(key)
        if record is not None:
            if probe_path and key in hidden and "stock" in record.get("answers", {}):
                record = probe.apply(probe_params, probe_thresholds, record, hidden[key], area)
                stats["probe_decisions"] += 1
            else:
                record = apply_half_rule(record, area_thresholds["areas"].get(area, area_thresholds["default"]))
            if empty_results is not None:
                record = apply_empty_rule(record, empty_results.get(key))
                seconds[camera, filename] += (empty_results.get(key) or {}).get("seconds", 0)
            seconds[camera, filename] += record.get("seconds", 0)
        stock = record and record.get("observed_stock")
        compliant = record and record.get("observed_compliance")
        model_mismatch = always_compliant and compliant is False
        product_checked = bool(record) and "compliance" in record.get("answers", {}) and not always_compliant
        stats["product_checked"] += product_checked
        if always_compliant and compliant is not None:
            compliant = True  # compliance check net-negative on labelled data (RESULTS, 10 Oct)
        fallback = stock is None or compliant is None
        stats["missing_result"] += record is None
        stats["stock_fallback"] += stock is None
        stats["compliance_fallback"] += compliant is None
        stats["empty_rule_changed"] += bool(record and record.get("empty_rule") and record.get("stock_before_empty_rule") != "empty")
        stats["half_rule_changed"] += bool(record and record.get("decision_rule") and record.get("stock_before_rule") != "half")
        stock = stock or FALLBACK_STOCK
        compliant = FALLBACK_COMPLIANT if compliant is None else compliant
        stats[f"stock_{stock}"] += 1
        stats["non_compliant"] += not compliant
        prediction = dict(planogram_compliant=compliant, stock_level=stock, stock_value=LEVELS[stock])
        submission.setdefault(camera, {}).setdefault(filename, {})[area] = prediction
        snapshots[camera, filename].append(dict(
            area_id=area, product_name=record["sample"]["product_name"] if record else None, **prediction,
            visibility=record.get("visibility", "unknown") if record else "unknown", fallback_used=fallback,
            crop_url=f"/assets/{camera}_{Path(filename).stem}_{area}.png", reference=None,
            reason=reason(record, stock, compliant, fallback, model_mismatch, product_checked)))
        stats["model_mismatch_suppressed"] += model_mismatch
    validate_submission(submission, expected)
    output.mkdir(parents=True)
    write_json(output/"submission.json", submission)
    write_json(output/"snapshots.json", [dict(
        snapshot_id=f"{camera}_{Path(filename).stem}", run_id=run_id, camera_id=camera, image_file=filename,
        captured_at=datetime.fromtimestamp(int(Path(filename).stem), timezone.utc).isoformat(),
        processed_at=processed, prediction_source="saved", context_mode="current_image_only",
        product_check="model" if stats["product_checked"] else "not_assessed",
        image_url=f"/assets/{camera}_{filename}", areas=areas) for (camera, filename), areas in snapshots.items()])
    per_image = sorted(seconds.values())
    report = dict(run_id=run_id, areas=len(expected), images=len(snapshots), decision_rule=f"half_if_stock_B>={HALF_THRESHOLD}",
                  compliance="always_true" if always_compliant else "model",
                  empty_rule=f"empty_if_v4_A>={EMPTY_THRESHOLD}" if empty_results is not None else None,
                  area_thresholds=len(area_thresholds["areas"]), probe=str(probe_path) if probe_path else None,
                  fallback=dict(stock=FALLBACK_STOCK, compliant=FALLBACK_COMPLIANT), counts=dict(stats),
                  seconds_per_image=dict(p50=per_image[len(per_image)//2], p95=per_image[int(0.95*(len(per_image)-1))],
                                         total=sum(per_image)) if per_image else None)
    write_json(output/"report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    a = sub.add_parser("inputs")
    a.add_argument("--prepared", type=Path, default=Path("data/prepared-v1"))
    a.add_argument("--dataset", type=Path, default=Path("new_dataset_hackathon_junctionx_10_oct_2026_v2"))
    a.add_argument("--output", type=Path, required=True)
    b = sub.add_parser("outputs")
    b.add_argument("results", type=Path)
    b.add_argument("--prepared", type=Path, default=Path("data/prepared-v1"))
    b.add_argument("--output", type=Path, required=True)
    b.add_argument("--run-id", required=True)
    b.add_argument("--probe", type=Path, help="Stock probe (ml/probe.npz + .json); needs --hidden")
    b.add_argument("--hidden", type=Path, help="Hidden states of this run (.npz from --save-hidden)")
    b.add_argument("--area-thresholds", type=Path, help="Per-shelf half thresholds (ml/area_thresholds.json)")
    b.add_argument("--empty-results", type=Path, help="Results of the prompt-v4 empty check (second stock question)")
    b.add_argument("--always-compliant", action="store_true", help="Answer compliant everywhere; model mismatch kept only as an app hint")
    args = parser.parse_args()
    if args.mode == "inputs":
        build_inputs(args.prepared, args.dataset, args.output)
    else:
        build_outputs(args.prepared, args.results, args.output, args.run_id, args.always_compliant, args.empty_results, args.area_thresholds,
                      args.probe, args.hidden)
