# Credit Burners — Fresh eyes on fresh produce

JunctionX Lisbon 2026 · Sensei challenge · Two-person team: Member1 (ML/evaluation) and Member2 (API/UI/deployment).

Existing ceiling cameras → for every planogram area: **is the shelf empty, half or full?** → a prioritised task list for store staff, with the photo as evidence. An open vision-language model (Qwen3.8-27B) runs on one GPU; decisions follow Sensei's own cost table (calling stock too high costs 3, too low costs 2).

## Results (our labelled data, not the official score)

| | Stock correct | Points (% of max) |
|---|---|---|
| **Blind random check** (50 shelves, labelled without seeing predictions) | **78%** | **61%** |
| Previous pipeline on the same 50 | 74% | 53% |
| "Always full" baseline | 78% | 53% |

- Processing cost: **3.8 s per camera image** on one NVIDIA RTX PRO 6000 (≈11 shelf areas per image), down from 16 s earlier in the day.
- Product identity is **not** assessed: every area is answered compliant (a product check produced more false alarms than catches on our labels).
- Labels are our own (348 observations); the official score comes only from Sensei's hidden validation. Every experiment, kept or rejected, is in [`docs/RESULTS.md`](docs/RESULTS.md).

## How it decides

1. **Crop** each planogram area from the camera image (perspective-corrected, out-of-view pixels masked).
2. **Ask** Qwen3.8-27B one multiple-choice question per area — empty / half / full — showing the camera view (640 px, area outlined), the crop and the mask. We read the answer probabilities, not generated text.
3. **Cost rule:** answer *half* unless the model is confident enough that the shelf is full. Sensei charges 3 for over-estimating and 2 for under-estimating, so half is the cheaper answer whenever P(really half) ≥ 3/7; on our labels that crossing sits at a model half-score of 0.20. Each shelf area gets its own threshold where our labels of that shelf show it is judged more or less strictly (`ml/area_thresholds.json`, no timestamps used).
4. **Empty check:** a second question encoding the stock definition (*empty = about one purchase left*) is asked only when the first answer is not confidently full, reusing the same image prefix; it overrides to empty when ≥ 70% sure.
5. **Never skip an area:** if anything fails, the area gets the fixed fallback (half, compliant) — a missing area costs 5.

## Run it on the validation images

### Requirements
- Linux with an NVIDIA GPU with ≥ 64 GB memory (tested on RTX PRO 6000 Blackwell, 96 GB), Python 3.11, PyTorch with CUDA, `transformers` ≥ 5.19, `accelerate`, Pillow.
- The model: `hf download Qwen/Qwen3.8-27B --local-dir models/qwen3.8-27b` (≈ 55 GB).
- Images at 1280×720 in camera-id folders (`6215/1751052241.jpg`, …) or flat (cameras are then matched to the supplied images; run `python3 -m ml.prepare new_dataset_hackathon_junctionx_10_oct_2026_v2 --output data/prepared-v1` first). A ZIP works too.

### One command (any GPU machine)
```bash
python -m ml.run <validation-images-folder-or-zip> --output out/final --model models/qwen3.8-27b
```
Writes `out/final/export/submission.json` in Sensei's exact format (camera → image → area → `planogram_compliant`, `stock_level`, `stock_value`), checked to cover every planogram area of every image, plus `snapshots.json` for the app and `crops-sheet.jpg` for a visual check. It stops with a clear error on images that are not 1280×720 or whose camera cannot be identified (`--allow-other-size`, `--trust-inferred-cameras` override after checking the crops sheet). If the model cannot run, a complete fallback submission is still written. 26 images take about 2 minutes.

### Team shortcut (laptop → knuth)
```bash
scripts/run_validation.sh <images-folder-or-zip> <name>    # → data/val-<name>/export/submission.json
```
Uploads only the raw images to our GPU server, runs the same pipeline there, opens the crops sheet during inference (Ctrl-C if crops look wrong) and fetches the result. Rehearsed: 26 images / 281 areas in 2 min 11 s; if the server is unreachable it writes a complete fallback submission and prints `!!!`.

## Reproduce our evaluation

```bash
python3 -m pip install -r ml/requirements.txt
python3 -m ml.prepare new_dataset_hackathon_junctionx_10_oct_2026_v2 --output data/prepared-v1
bash scripts/smoke_test.sh                                   # synthetic checks of preparation, geometry, scoring
python3 -m ml.compare_runs <results.json> …                  # score runs on our frozen labels (labels stay local)
```
Full-dataset predictions of the current pipeline: `results/qwen3.8-27b-ctx640-perarea-emptycheck-shared-alwayscompliant-full-v1/` (`submission.json`, `snapshots.json`, `report.json`). Experiment log with exact commands: [`docs/RESULTS.md`](docs/RESULTS.md).

## Repository map

| Path | What |
|---|---|
| `ml/run.py` | One-command validation run (prepare → infer → export) |
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

Open http://127.0.0.1:8080. The packaged Spring app serves React and the snapshot API from one origin. It reads the recommended `results/qwen3.8-27b-ctx640-perarea-emptycheck-shared-alwayscompliant-full-v1/snapshots.json` at startup, with images from `data/prepared-v1/assets`; restart after changing results. Override the JSON source with `--sensei.snapshots-file=<path>` (for the old baseline: `data/prepared-v1/snapshots.json`). All referenced assets in that prepared folder are served locally; curate an approved subset before public hosting. Unknown asset/snapshot IDs are rejected. No GPU worker is required.

With the app running, `python3 api/verify.py` checks real snapshot/detail/assets and frontend delivery. For UI development, `npm run dev --prefix ui` proxies API/assets to port 8080. The default is Member1’s saved stock predictions. Fallback areas remain unassessed. This run does not check product identity; the UI shows stock tasks without claiming verified product matches. Manual UI preview is opt-in with `?demo=1`.

For a phone on the same trusted Wi-Fi, start with `--server.address=0.0.0.0` and open `http://<Mac-LAN-IP>:8080`. Obtain that IP with `ipconfig getifaddr en0`. This exposes the prepared gallery to reachable devices; public hosting still requires an approved asset subset. The Java package uses `controller`, `service`, `repository` and `dto` layers under `team.creditburners`.

For continuation, start with the Member2 continuation section in `docs/PLAN.md`; current UI flow, validation handoff and known limitations are in `docs/DEMO.md`.
