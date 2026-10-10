"""Validation images -> Sensei submission.json, on one machine (no SSH). Needs an NVIDIA GPU (~60 GB) for the model.

  python -m ml.run <images-folder-or-zip> --output <new-dir> [--model <Qwen3.8-27B dir or HF id>]

Steps: prepare crops for every planogram area of every image (ml.validate), ask the stock question and the
conditional empty check from one shared image prefix (ml.infer_sample), export with per-shelf half thresholds and
always-compliant (ml.export). If inference fails, the export still writes a complete fallback submission.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path
from ml.export import build_outputs
from ml.validate import prepare_validation

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("images", type=Path, help="Folder or ZIP of camera images (camera-id folders, or flat)")
    parser.add_argument("--output", type=Path, required=True, help="New directory for crops, results and submission")
    parser.add_argument("--model", default="Qwen/Qwen3.8-27B", help="Local model directory or Hugging Face id")
    parser.add_argument("--dataset", type=Path, default=ROOT / "new_dataset_hackathon_junctionx_10_oct_2026_v2",
                        help="Folder with planogram.json")
    parser.add_argument("--references", type=Path, default=ROOT / "data/prepared-v1/assets",
                        help="Prepared supplied images, used only to identify cameras of flat (folderless) inputs")
    parser.add_argument("--allow-other-size", action="store_true")
    parser.add_argument("--trust-inferred-cameras", action="store_true")
    args = parser.parse_args()
    started = time.perf_counter()

    prepare_validation(args.images, args.dataset, args.output, args.references, args.allow_other_size, args.trust_inferred_cameras)
    print(f"Check {args.output / 'crops-sheet.jpg'}: every crop should show a produce shelf.", flush=True)

    results, empty = args.output / "results.json", args.output / "results-empty.json"
    command = [sys.executable, "-B", "-u", "-m", "ml.infer_sample", str(args.output / "sample.json"), "--model", args.model,
               "--stock-prompt", "v1", "--paired-prompt", "v4", "--paired-output", str(empty), "--paired-only-if-full-below", "0.5",
               "--questions", "stock", "--context-max-side", "640", "--output", str(results)]
    status = subprocess.run(command, cwd=ROOT).returncode
    if status != 0 or not results.exists():
        print(f"!!! inference failed (exit {status}); missing areas get the fallback answer (half, compliant)", flush=True)
        if not results.exists():
            results.write_text("{}\n")

    build_outputs(args.output, results, args.output / "export", f"credit-burners-{args.output.name}", always_compliant=True,
                  empty_results_path=empty if empty.exists() else None, area_thresholds_path=ROOT / "ml/area_thresholds.json")
    print(f"DONE in {time.perf_counter() - started:.0f}s: {args.output / 'export/submission.json'}", flush=True)


if __name__ == "__main__":
    main()
