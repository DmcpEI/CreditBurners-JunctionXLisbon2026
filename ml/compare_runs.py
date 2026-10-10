"""Score inference runs on every frozen label group, with and without the half rule, plus per-area time."""
import argparse
import json
import statistics
from pathlib import Path
from ml.decision_rule import apply_half_rule
from ml.evaluate_review import evaluate

LABELS = tuple(Path(f"data/ground-truth/human-v{v}-frozen.json") for v in (2, 3, 4))
# corrections under the refined stock definition: override only the listed observations (frozen originals untouched)
CORRECTIONS = (Path("data/ground-truth/human-r2-corrections-frozen.json"),)


def groups(paths=LABELS, corrections=CORRECTIONS):
    fixed = {x["id"]: x["label"] for path in corrections if path.exists() for x in json.loads(path.read_text())["items"]}
    result = []
    for path in paths:
        items = json.loads(path.read_text())["items"]
        for split in ("development", "holdout", "evaluation"):
            chosen = [{**x, "label": fixed.get(x["id"], x["label"])} for x in items if x["split"] == split]
            if chosen:
                result.append((f"{path.stem.split('-')[1]} {split}", chosen))
    return result


def labelled_manifest(full_manifest, output, paths=LABELS):
    """Subset of a full-run manifest covering every labelled observation, paths rewritten relative to output."""
    ids = {x["id"] for path in paths for x in json.loads(path.read_text())["items"]}
    rel = lambda value: str(Path("..") / full_manifest.parent.name / value)
    samples = [{**s, **{k: rel(s[k]) for k in ("context", "crop", "mask")}}
               for s in json.loads(full_manifest.read_text()) if s["sample_id"] in ids]
    if len(samples) != len(ids):
        raise ValueError("Some labelled observations are missing from the full manifest")
    output.mkdir(parents=True, exist_ok=True)
    (output / "sample.json").write_text(json.dumps(samples, indent=2) + "\n")
    print(f"{len(samples)} labelled inputs written to {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, nargs="*")
    parser.add_argument("--make-manifest", nargs=2, type=Path, metavar=("FULL_SAMPLE_JSON", "OUTPUT_DIR"))
    args = parser.parse_args()
    if args.make_manifest:
        labelled_manifest(*args.make_manifest)
        return
    gs = groups()
    print(f"{'run':44s}" + "".join(f"{name:>16s}" for name, _ in gs) + f"{'total':>7s}{'q/area':>8s}{'p50 s':>7s}")
    for path in args.results:
        results = json.loads(path.read_text())
        timed = [r for r in results.values() if not any(a.get("cache_hit") for a in r["answers"].values())]
        questions = statistics.mean(len(r["answers"]) for r in results.values())
        p50 = f"{statistics.median(r['seconds'] for r in timed):.2f}" if timed else "cache"
        for rule in (False, True):
            # groups the run does not fully cover are skipped (n/a), not failed
            scores = [evaluate(items, {x["id"]: apply_half_rule(results[x["id"]]) if rule else results[x["id"]] for x in items})
                      if all(x["id"] in results for x in items) else None for _, items in gs]
            print(f"{path.parent.name + '/' + path.stem + (' +rule' if rule else ''):44s}"
                  + "".join(f"{s['points']:>9}/{s['maximum']:<6}" if s else f"{'n/a':>16}" for s in scores)
                  + f"{sum(s['points'] for s in scores if s):>7}{questions:>8.2f}{p50:>7s}")


if __name__ == "__main__":
    main()
