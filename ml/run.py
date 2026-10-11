"""Validation images -> Sensei submission.json on one machine with an NVIDIA GPU (~60 GB). The submitted pipeline:

  python -m ml.run <images-folder-or-zip> --output <new-dir> --model <Qwen3.8-27B dir> --check-adapter <product-check adapter>

1. prepare crops for every planogram area of every image (ml.validate);
2. stock question with the fine-tuned adapter + empty check on the base model, from one image prefix (ml.infer_sample);
3. product check: trained crop/name adapter (ml.compliance_lora --adapter-in);
4. YOLO11n stock scores on square-padded crops (ml.yolo_cls predict);
5. export: YOLO (weight 0.6) and VLM stock averaged, half if >= 0.4, non-compliant if the product check is >= 0.99 sure
   (never on an area answered empty). The empty-check answers are still computed and saved (results-empty.json). Any failed step falls back (VLM missing -> YOLO; YOLO missing -> VLM; product
   check missing -> compliant); every area is always answered.
`scripts/run_validation.sh` runs the same steps with the GPU work on our server.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path
from ml.export import build_outputs
from ml.validate import prepare_validation

ROOT = Path(__file__).resolve().parent.parent


def step(command, log):
    with open(log, "w") as out:
        return subprocess.run([sys.executable, "-B", "-u", *command], cwd=ROOT, stdout=out, stderr=subprocess.STDOUT).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("images", type=Path, help="Folder or ZIP of camera images (camera-id folders, or flat)")
    parser.add_argument("--output", type=Path, required=True, help="New directory for crops, results and submission")
    parser.add_argument("--model", default="Qwen/Qwen3.8-27B", help="Local model directory or Hugging Face id")
    parser.add_argument("--adapter", type=Path, default=ROOT / "models/lora-stock-v2", help="Stock LoRA adapter (needs peft)")
    parser.add_argument("--check-adapter", type=Path, help="Product-check LoRA adapter (124 MB, on our server); omitted = compliant everywhere")
    parser.add_argument("--yolo", type=Path, default=ROOT / "models/yolo-stock-v1-pad.pt", help="YOLO stock classifier (needs ultralytics)")
    parser.add_argument("--dataset", type=Path, default=ROOT / "new_dataset_hackathon_junctionx_10_oct_2026_v2", help="Folder with planogram.json")
    parser.add_argument("--references", type=Path, default=ROOT / "data/prepared-v1/assets",
                        help="Prepared supplied images, used only to identify cameras of flat (folderless) inputs")
    parser.add_argument("--allow-other-size", action="store_true")
    parser.add_argument("--trust-inferred-cameras", action="store_true")
    args = parser.parse_args()
    started, out = time.perf_counter(), args.output

    prepare_validation(args.images, args.dataset, out, args.references, args.allow_other_size, args.trust_inferred_cameras)
    print(f"Check {out / 'crops-sheet.jpg'}: every crop should show a produce shelf.", flush=True)

    results, empty, check, yolo = (out / f"results{s}.json" for s in ("", "-empty", "-compliance", "-yolo"))
    if step(["-m", "ml.infer_sample", str(out / "sample.json"), "--model", args.model, "--adapter", str(args.adapter),
             "--stock-prompt", "v1", "--paired-prompt", "v4", "--paired-output", str(empty), "--paired-only-if-full-below", "0.5",
             "--questions", "stock", "--context-max-side", "640", "--output", str(results)], out / "inference.log") or not results.exists():
        print("!!! stock inference failed: YOLO answers alone (see inference.log)", flush=True)
        results.write_text("{}\n")
    if args.check_adapter and step(["-m", "ml.compliance_lora", str(out / "sample.json"), "--adapter-in", str(args.check_adapter),
                                    "--model", args.model, "--output", str(check)], out / "compliance.log"):
        print("!!! product check failed: compliant everywhere (see compliance.log)", flush=True)
    if step(["-m", "ml.yolo_cls", "predict", "--pad", "--weights", str(args.yolo), "--manifest", str(out / "sample.json"),
             "--output", str(yolo), "--device", "0"], out / "yolo.log"):
        print("!!! YOLO failed: VLM stock alone (see yolo.log)", flush=True)

    # decision settings tuned on Sensei's validation labels (11 Oct): YOLO weight 0.6, half >= 0.4, no empty check, product check >= 0.99
    build_outputs(out, results, out / "export", f"credit-burners-{out.name}", always_compliant=True,
                  area_thresholds_path=ROOT / "ml/lora_thresholds.json", compliance_path=check if check.exists() else None,
                  compliance_threshold=0.99, yolo_path=yolo if yolo.exists() else None, yolo_weight=0.6)
    print(f"DONE in {time.perf_counter() - started:.0f}s: {out / 'export/submission.json'}", flush=True)


if __name__ == "__main__":
    main()
