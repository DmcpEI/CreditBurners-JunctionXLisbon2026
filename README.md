# ShelfCue — fresh eyes on fresh produce

**Team Credit Burners** · JunctionX Lisbon 2026 · Sensei challenge (Member1: ML and evaluation, Member2: app and API).

ShelfCue turns a supermarket's existing ceiling cameras into a shelf assistant: for every shelf area in every camera image it decides **how full it is** and **whether it holds the right product**, and its phone app shows staff what to restock first, with the photo as evidence.

### 🌐 Try it: **[simon-provincial-once-usage.trycloudflare.com](https://simon-provincial-once-usage.trycloudflare.com)**

Open it on a phone. It's a simulated live view: the latest recorded image of each camera stands in for a live feed. Hosting notes are in `docs/DEMO.md`.

## The challenge

Sensei supplied 181 photos from 14 fixed cameras over the fruit and vegetable section of one store (27 June 2025, about one photo per camera per hour) and a planogram: 152 shelf areas, each a polygon in its camera image with the product that belongs there.

For every planogram area of every image, output in Sensei's exact JSON format:

- `planogram_compliant`: is exactly the planogram product there? (Anything else is non-compliant; a truly empty area is compliant.)
- `stock_level` / `stock_value`: `empty` 0, `half` 0.5, `full` 1. Organiser definition: *empty* = nothing or about one purchase left; *half* = still sellable, but staff would replenish now; *full* = not worth replenishing yet.

Scoring on a hidden validation set (26 images, 289 areas, same cameras; max 578 points):

| | Correct | Wrong |
|---|---|---|
| Identification | +1 | −2 |
| Stock | +1 | −2 if lower than the truth, −3 if higher |
| Missing area | | −5 |

The user interface (1–5) breaks ties. We run our code on the validation images and submit its output.

## How we tackled it

**1. From cameras to shelf crops.** Each planogram polygon is cut out of the camera image, perspective-corrected, with a mask for pixels outside the camera view (`ml/prepare.py`, `ml/validate.py`).

**2. Stock: two models, averaged.**
- A vision-language model, Qwen3.8-27B (open weights, one GPU), with a small LoRA adapter we fine-tuned on our labels, sees the camera view with the area outlined, the crop and the mask, and answers empty / half / full. We read its answer probabilities, not generated text.
- A YOLO11n classifier (3 MB, trained in minutes) sees the crop, padded to a square so the whole tray stays in view.
- Their probabilities are averaged. The two make different mistakes, so the average beats both (table below).
- **Cost rule:** too high costs 3 and too low costs 2, so in doubt we answer the lower level: *half* when the averaged half score is ≥ 0.4.
- **Empty check:** a second question written around "about one purchase left = empty" overrides to *empty* when the model is ≥ 70% sure.
- Training data: 348 shelf observations we labelled ourselves (344 with a stock level; 4 were hidden by fridge curtains), with our labelling page (`ml/label_set.py`, `ml/label_review.html`).

**3. Wrong product: trained, as the organiser asked.**
- Reviewing every image of 34 suspicious shelves found 149 wrong products in 435 images (≥ 7.7% of the day). Most are morning layouts with products shifted into neighbouring slots: kiwi packs in orange slots, oranges on the banana stand until about 08:00, onions in potato slots.
- With only a handful of human-labelled examples at the start, we made training pairs from our own images: a crop with its own planogram name means *this product*, the same crop with another shelf's name means *a different product* (half of them the same kind of produce, e.g. two banana or apple varieties).
- A second LoRA learns to answer "is this exactly the planogram product?" from the crop and the name. It sees no shelf position, so it must compare what it sees with the name.
- The area is marked non-compliant when the check is ≥ 60% sure, never when the area is answered empty.

**4. Never lose an area.**
- Every step has a fallback: VLM missing → YOLO alone; YOLO missing → VLM alone; product check missing → compliant; everything missing → half and compliant.
- The export checks it covers every expected area. `scripts/run_validation.sh` also waits for a free GPU, stops if image preparation fails and checks the 26 images / 289 areas.

**5. The app (ShelfCue).** A phone-first web app (React + Spring Boot) on the saved predictions:
- **Store view:** a simulated live view. The latest image of each camera, with urgent / soon counts, the shelves of a tapped camera, and every task linked to the crop and the camera photo with the shelf outlined.
- **Shelf study:** the recorded day for the whole store, a camera zone or a product. When shelves run low by hour, which products are most and least often low, where stock moves most, and the slowest refills. On 27 June shelves were fullest at 10:00 (76% full) and lowest at 19:00 (49%); an empty shelf waited a median 2 h 15 min to be refilled. Availability and restocking, not sales.

Product flags are part of the submission but kept out of the staff app. Details: `docs/APP.md`.

## Results (our own labels; the official score comes only from Sensei's validation)

**Stock:** 5-fold cross-validation over our 344 labels; each label is scored once by models that never saw it. Max 344 points.

| Stock method | Points | Correct | Too low / too high |
|---|---|---|---|
| **YOLO11n + fine-tuned Qwen (LoRA v2), averaged — submitted** | **255** | **319 (92.7%)** | 11 / 14 |
| YOLO11n alone | 245 | | |
| Fine-tuned Qwen alone (LoRA v2) | 199 | 305 (88.7%) | 11 / 28 |
| Fine-tuned Qwen, first adapter (LoRA v1) | 163 | 293 (85.2%) | 23 / 28 |
| "Always full" | −120 | 228 (66.3%) | 0 / 116 |

**Wrong product:** on the 435 reviewed images (149 wrong; the check never trained on these shelves) the check catches 72 wrong products. It raised no false alarms on 272 ordinary labelled shelves; 27 correct images on the suspicious shelves were flagged. That is about +126 points on the recorded day over answering "compliant" everywhere, ≈ +19 per 289 validation areas.

**Estimated official score:** ≈ 455–469 of 578 (79–81%), from stock 214–228 plus identification ≈ 241. This is an extrapolation from our own labels: the configuration was chosen on the same held-out predictions, our half/full judgement may differ from Sensei's, and the time of day of the validation images changes how many wrong products appear. Derivations: `docs/RESULTS.md`.

**Speed:** 26 validation images take about 3.5 minutes end to end on one RTX PRO 6000 (≈ 4 s per camera image for the VLM questions, 1 min for the product check, 3 ms per crop for YOLO on a laptop).

**Tried and dropped** (all measured in `docs/RESULTS.md`):
- prompt variants, product names and labelled reference photos in the prompt;
- a smaller VLM (Qwen3.5-4B), SAM 3 coverage, per-shelf thresholds, a hidden-state probe;
- an untrained product question (more false alarms than catches), YOLO as a product classifier;
- bigger YOLO models (no gain in the average);
- the mentor's unit-counting idea: SAM 3 instance counts with a learned adapter reach 140/344 alone but add only +2 to the average (branch `feat/unit-counting`);
- Claude Haiku / Sonnet / Opus zero-shot (Opus close to our earlier pipeline, at a per-image API cost and with store images leaving the premises).

## Run it

**Validation (what we run on submission day):**
```bash
scripts/run_validation.sh <images-folder-or-zip> <name>    # → data/val-<name>/export/submission.json
```
The script:
- uploads the raw images to our GPU server and runs the stock and product models there;
- runs YOLO on the laptop and exports;
- prints `!!!` for any fallback, and `OK` when the submission has the organiser's 26 images and 289 areas.

Rehearsed on 26 supplied images: identical to the full-dataset export.

**On any machine with an NVIDIA GPU (≥ 64 GB)**, the same pipeline in one command:
```bash
python3 -m pip install -r ml/requirements.txt
hf download Qwen/Qwen3.8-27B --local-dir models/qwen3.8-27b          # ≈ 55 GB
python3 -m ml.prepare new_dataset_hackathon_junctionx_10_oct_2026_v2 --output data/prepared-v1
python3 -m ml.run <images-folder-or-zip> --output out/final --model models/qwen3.8-27b --check-adapter <product-check adapter>
```
Notes:
- Images: 1280×720, in camera-id folders, flat, or a ZIP.
- The product-check adapter (124 MB) is above GitHub's file limit and lives on our server. Without `--check-adapter` every area is answered compliant.

**The app:**
```bash
npm ci --prefix ui && npm run build --prefix ui
mvn -f api/pom.xml package
java -jar api/target/shelfcue-0.1.0.jar --shelfcue.data-dir=data/prepared-v1 --server.address=127.0.0.1   # http://127.0.0.1:8080
```
`python3 api/verify.py` checks the running API. Public hosting through a Cloudflare tunnel is described in `docs/DEMO.md`.

**Our evaluation:**
- `bash scripts/smoke_test.sh` runs the unit checks.
- `python3 -m ml.lora_cv --score data/lora-cv --labels … --empty-results …` scores the cross-validation runs.
- Our labels stay local (`data/`, not in Git).

## Repository map

| Path | What |
|---|---|
| `ml/prepare.py`, `ml/validate.py` | Crops, masks and the expected-area list for the supplied and the validation images |
| `ml/infer_sample.py` | VLM questions (stock, empty check) with cached answers |
| `ml/finetune.py`, `ml/lora_cv.py` | LoRA fine-tuning and the 5-fold settings sweep |
| `ml/yolo_cls.py` | YOLO stock classifier: cross-validation, final training, prediction |
| `ml/compliance_lora.py` | Trained product check: pair generation, training, scoring |
| `ml/export.py`, `ml/decision_rule.py`, `ml/scoring.py` | Decisions (averaging, cost rule, empty check, product check), Sensei JSON export with coverage check, official scoring |
| `ml/run.py`, `scripts/run_validation.sh` | The submission pipeline: one machine, or laptop + GPU server |
| `ml/label_set.py`, `ml/label_review.html`, `ml/compare_runs.py`, `ml/evaluate_review.py` | Our labelling page and label bookkeeping |
| `models/lora-stock-v2/`, `models/yolo-stock-v1-pad.pt` | The two stock models in the submission |
| `results/…-productcheck-full-v1/` | Submission-format predictions for all 181 supplied images |
| `results/…-alwayscompliant-full-v1/` | The same stock for the app |
| `api/`, `ui/` | Spring Boot API and the ShelfCue React app |
| `docs/RESULTS.md` | Every experiment with numbers, kept or rejected (newest first) |
| `docs/APP.md`, `docs/CONTRACT.md`, `docs/DEMO.md` | App design, data formats and API, demo script and hosting |
| `docs/review/` | Our remaining held-out mistakes, with crop sheets, for error analysis |
| `new_dataset_hackathon_junctionx_10_oct_2026_v2/` | Sensei's supplied data: images (ZIP), planogram, challenge PDF |
