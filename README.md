# Credit Burners — Fresh eyes on fresh produce

JunctionX Lisbon 2026 · Sensei challenge · Two-person team: Member1 (ML/evaluation) and Member2 (API/UI/deployment).

Existing ceiling cameras → for every planogram area: **is the shelf empty, half or full?** → a prioritised task list for store staff, with the photo as evidence. An open vision-language model (Qwen3.8-27B) runs on one GPU; decisions follow Sensei's own cost table (calling stock too high costs 3, too low costs 2).

## Results (our labelled data, not the official score)

**Stock** — 5-fold cross-validation over all 344 labelled shelf observations: every label is scored once by a model that never saw it (max 344 points: +1 right, −2 too low, −3 too high).

| Stock method | Held-out points | Correct | Too low / too high |
|---|---|---|---|
| **YOLO11n-cls (whole tray) + fine-tuned Qwen (LoRA v2), averaged — submitted** | **255** | **319 (92.7%)** | 11 / 14 |
| YOLO11n-cls alone, whole tray (3 MB, trained in minutes) | 245 | | |
| YOLO11n-cls alone, default centre crop | 219 | 308 (89.5%) | 16 / 20 |
| Fine-tuned Qwen3.8-27B, LoRA v2 | 199 | 305 (88.7%) | 11 / 28 |
| Fine-tuned Qwen3.8-27B, LoRA v1 (morning of 11 Oct) | 163 | 293 (85.2%) | 23 / 28 |
| "Always full" | −120 | 228 (66.3%) | 0 / 116 |

**Wrong product** — the organiser's rule: anything that is not exactly the planogram product is non-compliant. Member1 reviewed every image of 34 suspicious shelves: 149 wrong products in 435 images (≈ 7.7% of the day, mostly products shifted into neighbouring slots in the morning). Our trained product check (never trained on those shelves) catches 72 of them (48%; 57% of those on non-empty shelves), with no false alarms on 272 ordinary labelled shelves: about +126 points on the recorded day over answering "compliant" everywhere (≈ +19 per 289 validation areas).

**Estimated official score:** ≈ 455–469 of 578 (79–81%): stock 214–228 (held-out rates × 289 areas, labelled vs random mix) + identification ≈ 241 (7.7% wrong products, product check on). An extrapolation from our own labels; the official validation is the only independent test. Derivations in [`docs/RESULTS.md`](docs/RESULTS.md).

- Processing cost: **≈ 3.5 minutes for the 26 validation images** end to end (rehearsed: 4 s per camera image for the VLM questions on one RTX PRO 6000, 1 min for the product check, 3 ms per crop for YOLO on a laptop).
- Labels are our own (348 observations, 344 with a stock level; 4 shelves hidden by fridge curtains) plus Member1's strict wrong-product review. Every experiment, kept or rejected, is in [`docs/RESULTS.md`](docs/RESULTS.md).

## How it decides

1. **Crop** each planogram area from the camera image (perspective-corrected, out-of-view pixels masked).
2. **Two stock opinions, averaged:** Qwen3.8-27B with our LoRA adapter answers empty / half / full from the camera view (640 px, area outlined), the crop and the mask (we read the answer probabilities, not text); a small YOLO11n classifier scores the crop (square-padded so the whole tray stays in view). Both were trained on our 344 labelled shelves.
3. **Cost rule:** Sensei charges 3 for over-estimating and 2 for under-estimating, so in doubt we answer the lower level: *half* when the averaged half score is ≥ 0.4.
4. **Empty check:** a second question encoding the stock definition (*empty = about one purchase left*), asked on the base model when the first answer is not confidently full; it overrides to empty when ≥ 70% sure.
5. **Product check:** a second LoRA, trained on crop + planogram-name pairs from our own images (a crop with its own name = right product, with another shelf's name = wrong), says whether the crop shows exactly the planogram product; ≥ 60% sure it does not → non-compliant. A truly empty area is always compliant.
6. **Never skip an area:** if anything fails, the area gets the fixed fallback (half, compliant) — a missing area costs 5.

## The app

A phone-first web app (React + Spring) on the saved predictions, two pages:

- **Store view — simulated live view.** The latest image of every camera stands in for a live feed (labelled "Simulated live · recorded data", red live dot, last-seen time). Camera cards show how many shelves need urgent / soon restocking and are sorted by urgency; tapping one lists only that camera's shelves, and every task opens the shelf crop and the camera photo with the shelf outlined. The bell lists every alert in the store.
- **Shelf study.** The recorded day studied for the whole store, one camera zone or one product: share of checks empty or half, median wait from empty to refilled, stock by hour, products most and least often low, where stock moves most, slowest refills. On 27 June (final model): shelves are fullest at 10:00 (76% full) and lowest at 19:00 (49%); an empty shelf waits a median 2 h 15 min to be refilled (11 refills seen; 13 not refilled by the last image). Availability and replenishment, not sales.

## Validation run

We run the pipeline ourselves when Sensei releases the validation images and commit the output (`submission.json`) to this repository; judges don't need to run anything. The commands below are for reproducing it.

### Requirements
- Linux with an NVIDIA GPU with ≥ 64 GB memory (tested on RTX PRO 6000 Blackwell, 96 GB), Python 3.11, PyTorch with CUDA, `transformers` ≥ 5.19, `accelerate`, Pillow.
- The model: `hf download Qwen/Qwen3.8-27B --local-dir models/qwen3.8-27b` (≈ 55 GB).
- Images at 1280×720 in camera-id folders (`6215/1751052241.jpg`, …) or flat (cameras are then matched to the supplied images; run `python3 -m ml.prepare new_dataset_hackathon_junctionx_10_oct_2026_v2 --output data/prepared-v1` first). A ZIP works too.

### One command (on a machine with that GPU)
```bash
python -m ml.run <validation-images-folder-or-zip> --output out/final --model models/qwen3.8-27b --adapter models/lora-stock-v1  # single-model path; the submitted hybrid runs through scripts/run_validation.sh
```
Writes `out/final/export/submission.json` in Sensei's exact format (camera → image → area → `planogram_compliant`, `stock_level`, `stock_value`), checked to cover every planogram area of every image, plus `snapshots.json` for the app and `crops-sheet.jpg` for a visual check. It stops with a clear error on images that are not 1280×720 or whose camera cannot be identified (`--allow-other-size`, `--trust-inferred-cameras` override after checking the crops sheet). If the model cannot run, a complete fallback submission is still written. The adapter needs `peft`; without `--adapter` the previous probe pipeline runs.

### Team shortcut (laptop → knuth)
```bash
scripts/run_validation.sh <images-folder-or-zip> <name>    # → data/val-<name>/export/submission.json
```
Uploads only the raw images to our GPU server, runs the same pipeline there, opens the crops sheet during inference (Ctrl-C if crops look wrong) and fetches the result. Rehearsed with the final pipeline: 26 images / 281 areas in 3 min 27 s, answers identical to the full-dataset export; if the server is unreachable it writes a complete fallback submission and prints `!!!`.

## Reproduce our evaluation

```bash
python3 -m pip install -r ml/requirements.txt
python3 -m ml.prepare new_dataset_hackathon_junctionx_10_oct_2026_v2 --output data/prepared-v1
bash scripts/smoke_test.sh                                   # synthetic checks of preparation, geometry, scoring
python3 -m ml.compare_runs <results.json> …                  # score runs on our frozen labels (labels stay local)
```
Full-dataset predictions of the current pipeline: `results/qwen3.8-27b-ctx640-lora-emptycheck-alwayscompliant-full-v1/` (`submission.json`, `snapshots.json`, `report.json`). Experiment log with exact commands: [`docs/RESULTS.md`](docs/RESULTS.md).

## Repository map

| Path | What |
|---|---|
| `ml/run.py` | One-command validation run (prepare → infer → export) |
| `models/lora-stock-v2/` | Fine-tuned stock adapter used in the submission (60 MB); `lora-stock-v1/` is the earlier one |
| `models/yolo-stock-v1-pad.pt` | YOLO11n crop classifier for stock (3 MB, square-padded crops), averaged with the LoRA; `yolo-stock-v1.pt` is the centre-crop version |
| `ml/yolo_cls.py`, `ml/lora_cv.py`, `ml/compliance_lora.py` | YOLO training/prediction, LoRA settings sweep (5-fold), trained product check (adapter on knuth: 124 MB, above GitHub's file limit) |
| `ml/prepare.py`, `ml/validate.py` | Crops, masks, expected keys; validation input handling and guards |
| `ml/infer_sample.py` | Qwen inference, cached per question; shared-prefix paired questions |
| `ml/decision_rule.py`, `ml/area_thresholds.py` | Cost-based half rule, empty check, per-shelf thresholds |
| `ml/export.py` | Sensei submission + app snapshots |
| `ml/label_set.py`, `ml/label_review.html`, `ml/evaluate_review.py`, `ml/compare_runs.py` | Annotation pages and scoring on our labels |
| `api/`, `ui/` | Spring Boot API and React app (see below) |
| `docs/` | Plan, contract, demo script, results |

## Member2 local app

Prepare the dataset above first. From the repository root:

```bash
npm ci --prefix ui
npm run build --prefix ui
mvn -f api/pom.xml package
java -jar api/target/sensei-0.1.0.jar --sensei.data-dir=data/prepared-v1 --server.address=127.0.0.1
```

Open http://127.0.0.1:8080. The packaged Spring app serves React and the snapshot API from one origin. It reads the recommended `results/qwen3.8-27b-lora2-yolopad-emptycheck-alwayscompliant-full-v1/snapshots.json` at startup, with images from `data/prepared-v1/assets`; restart after changing results. Override the JSON source with `--sensei.snapshots-file=<path>` (for the old baseline: `data/prepared-v1/snapshots.json`). All referenced assets in that prepared folder are served locally; curate an approved subset before public hosting. Unknown asset/snapshot IDs are rejected. No GPU worker is required.

With the app running, `python3 api/verify.py` checks real snapshot/detail/assets and frontend delivery. For UI development, `npm run dev --prefix ui` proxies API/assets to port 8080. The default is Member1’s saved stock predictions. Fallback areas remain unassessed. This run does not check product identity; the UI shows stock tasks without claiming verified product matches. Manual UI preview is opt-in with `?demo=1`.

For a phone on the same trusted Wi-Fi, start with `--server.address=0.0.0.0` and open `http://<Mac-LAN-IP>:8080`. Obtain that IP with `ipconfig getifaddr en0`. This exposes the prepared gallery to reachable devices; public hosting still requires an approved asset subset. The Java package uses `controller`, `service`, `repository` and `dto` layers under `team.creditburners`.

For continuation, start with the Member2 continuation section in `docs/PLAN.md`; current UI flow, validation handoff and known limitations are in `docs/DEMO.md`.
