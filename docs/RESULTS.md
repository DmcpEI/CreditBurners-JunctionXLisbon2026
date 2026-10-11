# Website verification — 11 October 2026

UI-only correction on the current LoRA export: known curtain frames 6383_1751001156 and 6386_1751001156 are treated as occluded. No labels, model outputs or submission files changed. Recomputed with `observations` / `summary` from `ui/src/features/snapshots/insights.js`: 1,947 usable checks (195 empty / 631 half / 1,121 full), 42.42% empty or half, 180 observed changes, 12 confirmed observed recoveries, median observation gap 134.78 minutes; 15 periods without confirmed recovery. These are differences between sampled model states, not measured sales or continuous empty durations. Earlier study figures below describe the pre-exclusion run.

Checks: 15 UI tests passed under `TZ=America/New_York`, including curtain exclusion/non-mutation, bilingual search and Lisbon midnight/daylight-saving times; production UI build and 15 ML smoke tests passed. API integration accepts either 400 or 404 for rejected encoded traversal paths, still requires 404 for unknown assets/IDs.

# Results

Latest rule update after the benchmark: truly empty areas are compliant; `ml/infer_sample.py` now implements this. Frozen labels and the historical numbers below are unchanged. Cost efficiency is now a judging criterion; see the Resume here section of `docs/PLAN.md` for the measurement protocol, provisional cost formula, model shortlist and next steps. No smaller VLM or YOLO benchmark has been run.

## LoRA settings sweep — round 1 done, round 2 running — 11 October 2026

`ml/lora_cv.py` on knuth: 5-fold CV over all 344 labels (seed 20261011; each label scored once by a model that never saw it), base model loaded once, one adapter per fold; out-of-fold scores in `data/lora-cv/<config>.json`. Scored with `python -m ml.lora_cv --score data/lora-cv --labels data/finetune-v1/labels.json --empty-results data/full-v1/results-probe-v4.json`: stock points (max 344) with the production empty check; "best" = half threshold chosen on the pooled out-of-fold scores (same optimism for all), plus the fixed production threshold 0.4.

| Config (round 1) | Best points (threshold) | At 0.4 | Correct |
|---|---|---|---|
| rank 16, lr 1e-4, 2 epochs | **216** (0.10) | 190 | 305 (88.7%) |
| rank 8, lr 2e-4, 2 epochs | 204 (0.25) | **199** | 304 (88.4%) |
| rank 8, lr 1e-4, 3 epochs | 197 (0.45) | 193 | 300 (87.2%) |
| **current** rank 8, lr 1e-4, 2 epochs | 186 (0.30) | 163 | 298 (86.6%) |
| current, 75% of training data | 181 (0.20) | 146 | 297 |
| rank 8, lr 5e-5, 2 epochs | 171 (0.35) | 156 | 295 |
| rank 8, lr 1e-4, 1 epoch | 150 (0.45) | 137 | 288 |
| current, 50% of training data | 119 (0.35) | 110 | 277 |

- **The adopted setting is undertrained:** every change that trains harder (rank 16, lr 2e-4, 3 epochs) gains 11–30 points; training less loses 15–36.
- **More labels:** 50% → 75% → 100% of the training folds gives 119 → 181 → 186; the curve flattens, so better settings beat a few dozen more labels.
- Seven of eight runs took 7 min per fold (3 epochs 10 min; 1 epoch or half data 3.6 min).
- **Round 2 (running, ≈ 3 h):** rank 16 + lr 2e-4, rank 16 + 3 epochs, lr 2e-4 + 3 epochs, and rank 16 with another training seed to size run-to-run noise. Adopt only a setting that wins robustly (at its best threshold and at a fixed one) and beats seed noise; then retrain on all 344, re-export, re-rehearse.

## Estimated official score (extrapolation) — 11 October 2026

Not a measurement: our held-out rates applied to 289 validation areas (max 578).
- **Stock:** LoRA mean stock points per true class on the 138 held-out labels (threshold 0.4 + empty check): full +0.736 (n = 91), half +0.273 (33), empty +0.143 (14). Held-out mix (66% full) → 0.565 per area → 163; reweighted to the random blind-50 mix (39 full / 8 half / 3 empty, 78% full) → 0.626 → 181; all-344-label mix → 0.567 → 164.
- **Identification:** always compliant; 10 wrong products in 330 labelled observations → (320 − 2·10)/330 = 0.909 per area → 263.
- **Missing areas:** none (rehearsal covered 281/281) → 0.
- **Total ≈ 426 (held-out mix) to ≈ 444 (random mix) of 578 (74–77%).** Chance alone moves this by about ±20 points; if Sensei's labels judge half vs full differently from ours, more. The official validation replaces this line.

## Store insights from one recorded day (app, Shelf study) — 11 October 2026

From the LoRA export with the app's `insights.js` (curtain frames 6383/6386 at 06:12 treated as occluded, Lisbon time; see Website verification): 1,947 usable shelf checks, 42% empty or half (195 empty / 631 half / 1,121 full). By hour: 06:00 28% empty / 34% full (overnight state), 09:00–10:00 2–3% empty / 70–72% full (restocked), 14:00 dip (11% empty, 55% full), 15:00–16:00 refilled (65–67% full), 19:00 19% empty / 41% full (evening run-down); 20:00 has only 9 checks. 180 lasting level changes after removing A-B-A flicker. Median wait empty → refilled 134.8 min ≈ 2 h 15 min (12 refills; 15 empty spells not refilled by the shelf's last image; slowest: Fuji apples 6385_4 > 7.5 h). Often low: papaya, shallot, sweet potato, guava, chayote, melon (some may be displayed half-full by design); rarely low: lime, cherry, potato, pumpkin, ginger. Most movement: cameras 6376 and 6491; least: 6371, 6386, 6781. Caveats: one day, hourly images, model estimates (88% stock accuracy held out); not sales.

## Wrong-product check retried — not adopted — 11 October 2026

- **Labels:** 10 wrong products in 330 labelled observations (3%), 9 areas, mostly category swaps (bananas in a citrus area, onions in a potato area, kiwi packs where orange nets belong); the same area is often compliant at other times. Flagging gains 3 per catch and costs 3 per false alarm, so it pays only above 50% precision; even perfect detection would add ≈ 24 points over 289 areas.
- **Question** (`ml/product_check.py`, base model): "is it clearly a different kind of fruit or vegetable?" with the English product name; variety, brand, pack size and labels explicitly do not count. 160 s for 330 observations, both image modes.
- **Ranking is good, precision is not:** camera view + crop AUC 0.90, crop only 0.88. Best net on the same labels: −12 (camera view, P(B) ≥ 0.95: 1 caught, 5 false alarms) and +3 (crop only, P(B) ≥ 0.95: 2 caught, 1 false alarm) — a threshold picked on the evaluation data itself, within noise. False alarms repeat on the same areas (apples `6385_9`, onions `6594_13`, bananas `6468_11`).
- **Per-area anomaly** (P(B) minus the area's median over other labelled times): AUC 0.70 / 0.55, worse; 4 of the 10 wrong products have no other labelled time of the same area.
- **Decision:** submission stays always compliant. Too few positives (10) to fine-tune a product check.

## LoRA adopted — final pipeline v7 — 11 October 2026

- **Final adapter** `lora-stock-v1` trained on all 344 labels (same settings as the folds, 8 minutes); half threshold 0.4 (`ml/lora_thresholds.json`, no per-shelf thresholds); the empty check (prompt v4, empty if A ≥ 0.7, asked when C < 0.5) runs on the base model with the adapter disabled, as evaluated.
- **Why:** 2-fold held-out stock points (138 labels: 14 empty / 33 half / 91 full; max 138) LoRA 78 vs probe 68 vs per-shelf 60. Same 138: LoRA 121 correct (88%), 8 too low, 9 too high; base model + global rule 0.2 + empty check 40 points (111 correct, 10 low / 17 high); always full −50 (91 correct, 47 too high). The app's "about 88% right" is this LoRA figure. No untouched check remains: the blind 50 are part of the 344 training labels (348 labelled observations minus 4 curtain-hidden ones without a stock level). The LoRA threshold 0.4 was chosen on training labels; the 3/7 cost crossover is the principle (half is cheaper when P(half) ≥ 3/7), measured on base-model scores, not where 0.4 came from.
- **Fresh run → app:** `run_validation.sh` now also copies the run's crops/photos back (`data/val-<name>/assets`, ≈ 99 MB for 26 images, 1.5 s) and prints the app command (`--sensei.data-dir=data/val-<name> --sensei.snapshots-file=data/val-<name>/export/snapshots.json`). Not yet rehearsed in the app.
- **Full export** `results/qwen3.8-27b-ctx640-lora-emptycheck-alwayscompliant-full-v1/`: 200 empty / 639 half / 1,123 full; 84% identical to the probe export, mostly full→half (243) — the cheaper direction under Sensei's costs. 8 areas (early images of cameras 6383/6386) answered D "can't tell" → fixed fallback (half).
- **Cost:** 822 s for 181 images incl. model load = 4.5 s per camera image (p50 3.8 s model time); the adapter path does not share the image prefix between the two questions.
- `ml.run --adapter` and `scripts/run_validation.sh` use the adapter; `ml.run` without `--adapter` keeps the probe pipeline.

## Claude models (agents) on the blind 50; LoRA fine-tuning — 10–11 October 2026

**Claude Haiku / Sonnet / Opus**, via isolated Claude Code agents (two per model, 25 items each) given only our exact stock prompt v1 and the anonymised images (640 px camera view with outline, crop, mask) of the blind 50; no repo context, no labels. Mimics an API call (not identical: agent harness, self-reported probabilities). Product answered compliant for all.

| Blind 50 | Stock correct | Points | Half | Full | Empty |
|---|---|---|---|---|---|
| Claude Haiku | 33/50 | 38/99 | 2/8 | 29/39 | 2/3 |
| Claude Sonnet | 37/50 | 53/99 | 4/8 | 30/39 | 3/3 |
| Claude Opus | 43/50 | 72/99 | 5/8 | 35/39 | 3/3 |
| our probe pipeline (fitted without the blind 50) | 44/50 | 75/99 | 6/8 | 36/39 | 2/3 |

Applying the cost formula to the agents' self-reported probabilities lowered every model (Opus 66/99). Opus zero-shot ≈ our probe pipeline (difference within ±5 noise); Haiku is below "always full" (52/99). Not adopted: no gain, per-image API cost, open questions on cloud APIs and sending store images to a third party. The blind 50 have now been used for several comparisons; further choices must not be made on them.

**LoRA fine-tuning** (`ml/finetune.py`, peft only in env `jx-fast`): rank 8 on the language model's attention projections (`q/k/v/o_proj`, `in_proj_qkv`, `out_proj`), target = answer letter, 2 epochs, lr 1e-4, accumulation 8, same inputs as production; 275 training labels, 7 minutes on the RTX PRO 6000. Held-out fold 0 (69 labels: 16 half, 46 full, 7 empty), stock points: global rule 16, per-shelf thresholds 20, probe + per-shelf 27, LoRA raw 23, **LoRA + empty check with half threshold 0.4 chosen on the training labels 32**. Both folds (138 held-out labels): **LoRA 78**, probe 68, per-shelf thresholds 60 stock points.

## Hidden-state probe adopted — final pipeline v6 — 10 October 2026

- **Point-loss analysis** (all 344 labels, per-shelf thresholds learned leave-one-out): 474/674 points (70%); lost: full→half 75 (38%), half→full 68 (34%), missed wrong products 30 (15%), missed empties 24 (12%). Worst products tomatoes (34) and citrus (28), mostly narrow packaged areas on cameras 6443/6376.
- **Probe** (`ml/probe.py`): the frozen Qwen3.8-27B's last-layer hidden state at the answer position (saved with `--save-hidden`, also in shared-prefix mode; cosine ≥ 0.997 vs a plain forward), standardised → PCA 16 + the four answer log-scores → logistic regression (C = 0.05). Decision: empty if P(empty) ≥ 0.5, else half if P(half) ≥ the shelf's threshold (default chosen on labels, per-shelf where strictly better), else full; then the production empty check. No extra GPU work.
- **Cross-validation, stock points (344 labels):** unseen timestamps (random 5-fold) 167–179 vs 163 for per-shelf thresholds on the answer scores; unseen shelves (area-grouped) 106–135 vs 101 (ranges: plain vs production-path vectors).
- **Blind 50, probe fitted without them:** **75/99 points (76%)**, stock 44/50 (half 6/8, full 36/39, empty 2/3) vs 60/99 for per-shelf thresholds and 52/99 for the global rule.
- **Adopted.** Final probe fitted on all 344 labels → `ml/probe.npz` + `ml/probe.json` (default half threshold 0.5 on probe probabilities, 20 per-shelf thresholds). Export `results/qwen3.8-27b-ctx640-probe-emptycheck-shared-alwayscompliant-full-v1/`: 206 empty / 429 half / 1,327 full; 240 decisions differ from the per-shelf export (134 half→full, 58 full→half, 44 →empty). `ml.run` and `scripts/run_validation.sh` save hidden states and use the probe (fallback: per-shelf half rule). Cost unchanged: 3.8 s per camera image.
- **Fine-tuning (LoRA)** experiment running (`ml/finetune.py`, peft in `jx-fast` only); **Claude Haiku/Sonnet/Opus** comparison on the blind 50 running via isolated agents.

## Blind final check and per-shelf thresholds adopted — final pipeline v5 — 10 October 2026

- **Blind set labelled** by Member1 (`data/ground-truth/human-final-frozen.json`, SHA256 `cccc3310ffd2…`): 50 random observations, 39 full / 8 half / 3 empty, 1 mismatch. Scored **once**, per-area thresholds fitted on the earlier 298 labels only:

| On the blind 50 | Stock correct | Points | % of max |
|---|---|---|---|
| current (global 0.20) | 37/50 (74%) | 52/99 | 53% |
| **per-area threshold** | **39/50 (78%)** | **60/99** | **61%** |
| per-area, ≥2 labels only | 38/50 | 57/99 | 58% |
| always full | 39/50 | 52/99 | 53% |

  Per-area fixes 2 half shelves without new full errors. On this random sample the global pipeline only ties "always full": random shelves are 78% full vs 64% in our labelled sets. Re-weighting labels to that natural mix still picks 0.20 on development (95.4 vs 92.6 at 0.30), so the global default stays.
- **Mentor (relayed):** "You will get the timestamp but the model should learn from the image itself and not necessarily the time of day." Per-shelf thresholds use no timestamp: the prediction comes from the image (model scores); only each shelf's strictness is learned from our labels of that shelf.
- **Adopted:** `ml/area_thresholds.py` fits per-shelf half thresholds on **all** labels (v2–v4 + r2 corrections + blind 50; refit after the blind check was used once) → `ml/area_thresholds.json`: 37 of 146 labelled areas deviate from 0.20 (0.02 ×15, 0.05 ×3, 0.1, 0.15, 0.3 ×14, 0.5 ×3). Export `--area-thresholds`; `scripts/run_validation.sh` uses it. No extra GPU work: **3.8 s per camera image**.
- Export `results/qwen3.8-27b-ctx640-perarea-emptycheck-shared-alwayscompliant-full-v1/` (166 empty / 544 half / 1,252 full; 14 fallbacks). Validation rehearsal 26 images in **2 min 11 s**, identical to the full export 281/281.
- **Honest expected performance:** leave-one-timestamp-out stock points 147 vs 78 (218 obs); blind check 61% vs 53% of max points. Scores on the labels used for fitting are optimistic and not reported as results.

## Research report follow-up: calibration, per-area thresholds, blind final set — 10 October 2026

Deep-research report (`~/Downloads/deep-research-report (2).md`, not in repo): hidden validation reuses the same 152 areas from the same day, so area-specific correction and score-optimal calibration rank first; test area-specific methods by leaving timestamps out within an area, not by area-grouped splits.

- **Label coverage:** 146/152 areas have ≥1 stock label (6 none, 76 one, 33 two, 16 three, 21 four or more); 218 observations sit in areas with ≥2 labels.
- **Calibrated expected-utility decision** (multinomial logistic on log-scores of both questions, trained on development, U(E)=3pE−2, U(H)=−3pE+pH−2pF, U(F)=4pF−3): stock points holdout −4…3 vs 3, evaluation 5–12 vs 25, development area-grouped 5-fold CV 54 vs 67. **Rejected**; the half rule is already close to optimal.
- **Per-area half threshold** (choose each area's threshold from {0.02…0.5, none} on its other labelled timestamps; keep 0.20 unless strictly better), leave-one-timestamp-out on the 218 observations, stock points: **147 vs 78** for the global rule (development 109 vs 57, holdout 17 vs 3, evaluation 21 vs 18); requiring ≥2 other frames: 144. Copying the nearest labelled timestamp's label scores −2 (stock really changes during the day), so the gain is not label copying. Chosen thresholds: 0.02 ×37, 0.05 ×9, 0.1 ×3, 0.2 ×156, 0.3 ×10, 0.5 ×3. **Promising, not adopted yet**: needs the blind final check and a mentor answer on using our own labels of the same areas at other times.
- **Blind final set:** `data/human-review-final/` (set `332e7fd946552d54`, protocol `sensei-replenish-v5`, port 8770): 50 random unlabelled observations (seed 20261010; 3 per camera + 8 random; curtain frames excluded), no suggestions and no reference labels shown; 48 of them are new timestamps of already-labelled areas (like the hidden validation). Score candidate pipelines on it once, after labelling.

## Labelled reference crops in the stock question — 10 October 2026

Four human-labelled development crops shown before the target (`--references data/references-v1/refs.json`): full tomatoes `6443_1751001244_6443_1`, half apples with empty cups `6385_1751051814_6385_1`, half sweet potatoes with bare floor `6591_1751013255_6591_6`, empty single banana bunch `6215_1751001268_6215_1`. Prompt v1, 640 px, all 298 labelled areas; empty check from the existing answers; reference areas excluded from development for both versions (141 development observations).

| | Dev (best threshold) | Holdout | Eval | s/area (stock question) |
|---|---|---|---|---|
| current (no references) | **183** (0.20) | **41** | 91 | 0.24 |
| with references | 140 (no rule) | 20 | 77 | 0.42 |

**Not adopted.** With references the model calls even more shelves full (half recall 17/71 vs 40/71), and it is 75% slower. Together with the bare-floor wording, product names and the organiser-wording prompts, prompt-side changes have not beaten the cost-justified half rule on development. Files: `data/labelled-v2/refs-v1.json`.

## Astra review fixes, conditional empty check — 10 October 2026

- **Independent check (Astra):** current export on corrected labels: stock 240/294 (82%; empty 25/30, half 43/75, full 172/189), 349/575 points vs 128/575 for always full + compliant. Main weakness: 32 half→full errors.
- **Half→full errors cluster by area:** of 19 on development, 14 come from 5 areas labelled half all day while the model says full all day: purple cabbage basket `6386_3` (5), lemons `6376_1` (3), red pepper basket `6383_5` (2), Gala tray `6373_1` (2), mango box `6462_3` (2) (`data/labelled-v1/dev-half-full-errors.json`). Candidate next step: a few human-approved reference examples for half vs full; not run yet.
- **Honest product status:** export `reason` now says "product identity not checked (answered compliant by policy)"; snapshots carry `product_check: "not_assessed"`; run id contains `alwayscompliant`. Submission unchanged.
- **Validation guards:** non-1280×720 images and unclear camera matches (next/best distance < 1.3; rehearsal minimum 1.69) now stop the run; `crops-sheet.jpg` of all crops is written and opened during inference; `VALIDATE_FLAGS` for deliberate overrides.
- **Conditional empty check** (`--paired-only-if-full-below 0.5`, screened on cached answers first: thresholds 0.5–0.99 lost no empty overrides on all 1,962 areas): empty check asked for 381/1,962 areas; **final submission identical** to the always-on export; **3.81 s per camera image** (p95 6.54; was 4.82). Validation rehearsal 26 images in **2 min 14 s**, identical 281/281.
- No truly fresh test areas remain (~6 unused); holdout and evaluation have been seen in many comparisons, so report them as such.

## English product name in the stock prompt — 10 October 2026

Prompts `v1n` / `v4n` = v1 / v4 plus "The planogram product for this area is {English name}" (`ml/products_en.json`). Shared-prefix runs on the 298 labelled areas, 640 px, corrected labels, half 0.20 / empty 0.70:

| Variant | Dev | Holdout | Eval | All | s/area (both q) |
|---|---|---|---|---|---|
| current (no name) | **217** | **41** | 91 | **349** | 0.482 |
| name in both questions | 207 | 24 | 107 | 338 | 0.492 |
| name in stock question only | 207 | 24 | 107 | 338 | 0.494 |

Best re-tuned thresholds on development: 209 (half 0.15, empty 0.9) vs 217 for the current pipeline. **Not adopted** (worse on development and holdout; the evaluation gain is not used for selection). The name does not change the empty check's decisions. Files: `data/labelled-v2/names-*.json`.

## Speed with the empty check: batching vs shared prefix — 10 October 2026

All 298 labelled areas, 640 px, both questions (v1 stock + v4 empty check), corrected labels:

| Option | Both questions per area | Dev | Holdout | Eval | Unchanged answers v1 / v4 |
|---|---|---|---|---|---|
| unbatched (previous) | 0.581 s | 205 | 38 | 94 | — |
| batch 4 / 8 / 16 | 0.483 / 0.499 / 0.512 s | 209 / 205 / 205 | 38 / 37 / 37 | 91 / 94 / 94 | 292 / 289 at batch 4 |
| **shared prefix** (`--paired-prompt v4 --paired-output …`) | **0.482 s** | 217 | 41 | 91 | 296 / 292 |

- Shared prefix: the images and description text are prefilled once; each question continues from a deep copy of the cache (positions continue from the cache length + stored M-RoPE offset, no attention mask on the continuation). Adopted: same speed-up as the best batch, closest to the original answers, no score loss; one model load per run. Score differences across options are borderline numeric noise.
- **Full dataset:** p50 **4.82 s per camera image** (p95 7.77; was 5.75), corrected labels 217 / 41 / 91; 1,897/1,962 final answers identical to the separately computed export. Export `results/qwen3.8-27b-ctx640-half020-emptycheck-shared-full-v1/` (165 empty / 498 half / 1,299 full, 15 fallbacks). `scripts/run_validation.sh` uses one paired call: rehearsal 26 images / 281 areas in **2 min 36 s**, identical to the full export 281/281.

## Corrected labels, empty check — final pipeline v4 — 10 October 2026

- **Corrections:** Member1 confirmed the 27-flag re-check under the refined definition: 24 suggestions accepted, 3 old labels kept (#13 2–3 banana bunches stay empty, #51 ~3 apple bags stay empty, #72 single kiwi bag stays full). Frozen as `data/ground-truth/human-r2-corrections-frozen.json` (SHA256 `e010889783db…`, protocol `sensei-replenish-v5`); `ml/compare_runs.py` overlays it on the v2–v4 frozen labels (originals untouched).
- **Prompts on corrected labels (640 px; best threshold chosen on development):** v1 at 0.20: dev 201 / holdout 34 / eval 85; v3 at 0.40: 201 / 33 / 82; v4 (refined rule) at 0.40: 183 / 18 / 81. v1 kept. Calibration on corrected dev labels: P(really half) 31% for B 0.15–0.20, **46% for 0.20–0.30** (crosses 3/7), so 0.20 still follows from the cost table.
- **Empty check adopted:** prompt v4 on its own catches more empty shelves (28/30 vs 23/30 for v1 alone; the released v1 + rules + empty-check pipeline catches 25/30) but is worse on half/full. Rule: answer empty when the v4 answer's empty score A ≥ 0.70, otherwise v1 + half rule (`ml/decision_rule.py apply_empty_rule`, chosen on development): **dev 205 / holdout 38 / eval 94 (all 337) vs 201 / 34 / 85 (320)**, gains on every group. Cost: two stock questions per area, ~5.8 s per camera image (v1 alone 2.9 s).
- **Built and verified:** full-dataset prompt v4 run matches the labelled run (298/298 decisions); export `results/qwen3.8-27b-ctx640-half020-emptycheck-full-v1/` scores exactly 205 / 38 / 94 on corrected labels; 166 empty / 498 half / 1,298 full, 27 decisions changed by the empty check, 16 fallbacks. **Measured cost: 5.75 s per camera image** (p95 9.3 s), both questions, model time only. `scripts/run_validation.sh` asks both questions: rehearsal 26 images / 281 areas in **3 min 16 s**, identical to the full export 281/281; offline fallback still writes a complete submission.

## Final pipeline v3: 640 px context; label re-check under organiser definition — 10 October 2026

- **Full-dataset runs, 640 px context** (stock-only, prompt v1, half rule 0.20, always compliant): standard env `jx` p50 **2.87 s per camera image** (p95 4.66), 0.29 s per area, 10.6 min wall for 1,962 areas incl. load; `jx-fast` (flash-linear-attention) 2.37 s per image, 8.9 min. Development identical (207 vs 207), holdout 32 vs 28, evaluation 90 vs 87, 71/1,962 decisions differ. **Adopted: standard env** (same score, no extra dependency or JIT compile in the final run); kernels kept as an 18% speed option.
- Export: `results/qwen3.8-27b-stockonly-ctx640-half020-full-v1/` (139 empty / 518 half / 1,305 full, 16 fallbacks); contract updated. `scripts/run_validation.sh` now uses `--context-max-side 640`; rehearsal 26 images / 281 areas in **1 min 40 s**, identical to the full export 281/281.
- Cost per image over the day: 16 s (4 questions, 1280 px) → 5.5 s (stock only) → **2.9 s** (640 px context).
- **Label re-check under the organiser definition.** All 294 labelled visible crops reviewed by the assistant; 35 flagged (`data/labelled-v1/relabel-flags.json`): 15 labelled empty where what is left is still sellable (5 strong: sellable banana bunches, ~6 cucumbers, apple bags, potato bags) → half; 12 labelled full where staff would refill now (big-fruit crates with bare floor, mangoes, aubergines, cabbage frames inconsistent with the same area's half frames) → half; 8 labelled half that look fully stocked → full (weakest; "in doubt lower" keeps half defensible). Main systematic shift: sealed packs/bags remain sellable, so a few left is half, not empty. Re-check page `data/human-review-r1/` (set `6634ae66a71f84dc`, protocol `sensei-replenish-v4`, port 8768; built with `python3 -m ml.label_set --revision-flags data/labelled-v1/relabel-flags.json --labels …v2… --labels …v3… --labels …v4… --output data/human-review-r1`). Frozen labels unchanged; confirmed answers become a correction version overriding only those 35. Prompt v1 vs v3 and the threshold must be re-scored on the corrected labels.
- **Superseded by the refined rule** (about one purchase left = empty): re-checked all 102 empty/half labels again; **27 flags** (`data/labelled-v1/relabel-flags-v2.json`): empty→half 4 (2–3 banana bunches, ~6 cucumbers, 3–4 apple bags strong; ~3 apple bags possible), half→empty 3 (one melon strong; one banana bunch, 1–2 lettuce bags possible), full→empty 1 (single kiwi net bag), full→half 11, half→full 8 (weakest). Single packs/bags/bunches previously flagged empty→half now stay empty. Page `data/human-review-r2/` (set `7c7e46866630cfb2`, protocol `sensei-replenish-v5`, port 8769); r1 (port 8768) withdrawn. Stock prompt v4 in `ml/infer_sample.py` encodes the refined rule; to be scored on the corrected labels.

## Error analysis, cost-justified rule, efficiency — 10 October 2026

Current pipeline (stock question only + half rule v2 + always compliant) on all 294 labelled visible stock observations (`data/labelled-v1/error-rows.json`).

**Errors are on the half/full boundary.** 228/294 correct (78%). Confusion (truth → prediction): empty 23/5/1, half 0/46/27, full 0/33/159. Over-estimates (shelf runs out unnoticed, −3 each): 33 → −99 points; under-estimates (useless restock trip, −2 each): 33 → −66. Worst cameras: 6371 melons/watermelons 10/21 wrong, 6376 citrus/kiwi packs 9/22, 6468 exotic fruit 8/22. Packaged vs loose error rate similar (18/77 vs 48/217).

**The decision rule follows from the store's costs.** Sensei's table charges 3 for calling stock higher than reality (lost sales) and 2 for calling it lower (wasted staff trip). Between half and full, "half" is the cheaper answer whenever P(really half) ≥ 3/7 ≈ 43% (with h + f = 1: expected points of answering half = h − 2f, of answering full = f − 3h, so half wins when 4h > 3f, i.e. h > 3/7). Measured P(really half) by the model's half score B (half/full truths, all labels): B<0.02: 6% · 0.02–0.05: 9% · 0.05–0.10: 14% · 0.10–0.15: 23% · 0.15–0.20: 35% · **0.20–0.30: 43%** · 0.30–0.50: 53% · ≥0.50: 74%. It crosses 3/7 at B ≈ 0.20, the threshold already chosen on development. Pitch line: *we answer "half" unless the model is confident enough that the shelf is full, where "confident enough" is set by the store's cost of a missed stock-out vs a useless trip and by measured accuracy on 294 labelled shelves.* Empty side: P(really empty | empty score A) is 96% for A ≥ 0.4 and ≤ 33% below, so the same 3/7 bar leaves the model's empty answers unchanged (only 1 missed empty would flip).

**Annotation check.** 18 observations where the model is very sure and disagrees (`data/labelled-v1/suspects.json`), reviewed visually by the assistant: label probably wrong 2 (`6383_1751044960_6383_9` cucumbers labelled empty, ~6 visible; `6371_1751044440_6371_3` melon labelled full with bare floor), leaning wrong / borderline 4 (lemons `6376_1751029801_6376_1`, Gala `6373_1751040770_6373_1`, Portuguese cabbage `6383_1751013620_6383_4`, `6383_1751044960_6383_4`), model clearly wrong 5, genuinely ambiguous half/full 7. Boundary noise exists but nothing systematic; frozen labels unchanged (any correction must be a new labelled version by Member1).

**Efficiency.**
- Batching (`--batch-size`, stock-only, left padding): p50 0.524 / 0.535 / 0.540 s per area at batch 4 / 8 / 16 vs 0.551 at batch 1, and 3–5 of 200 decisions change from padding numerics. Not adopted: prefill with three images is already compute-bound.
- Smaller camera context (`--context-max-side`, all 298 labels, half rule 0.20): 1280 px dev 201 / holdout 35 / evaluation 81 at 0.55 s per area; **640 px dev 207 / 32 / 90 at 0.28 s** (adopted); 448 px (200 labels only) dev 84 vs 100, rejected. The 0.20 threshold still sits at the 3/7 crossing for 640 px answers.
- **Stock prompt v3 from the organiser's definition** (customer would not buy → empty; staff would replenish now → half; else full; in doubt lower), 640 px: without a rule it beats v1 on every group (dev 181 vs 177, holdouts 22 vs 2, evaluation 95 vs 90), but it already shifts mass to half, so v1's 0.20 threshold over-calls half (dev 177). Its own calibration crosses 3/7 near B ≈ 0.4; best v3 on development: threshold 0.4, dev 193 < 207 for v1 + 0.20. **Not adopted**; the definition backs the decision rule in the pitch instead. Files: `data/labelled-v2/stock-v3-ctx640.json`.
- Kernel packages: model logs say `flash-linear-attention` / `causal_conv1d` fall back to slow reference code. `flash-linear-attention` 0.5.2 installed in a cloned env `jx-fast` on knuth (`jx` untouched): p50 0.438 vs 0.551 s per area (1280 px), one-time 23 s compile on the first area, 196/200 decisions identical (small numeric differences). Full-dataset 640 px comparison with/without it running.

**Member2 review (10 Oct).** Spring API serves only snapshot-referenced assets with a strict ID pattern and real-path check; React app (Store view: latest image per camera with tasks/polygons/evidence; Shelf study: per-camera history and stock timeline) reads `results/qwen3.8-27b-stockonly-half020-full-v1/` and labels stock-only runs as "product not assessed". UI unit tests 9/9 pass with `node --test ui/tests/*.test.js`; `npm run build` succeeds. Java/Maven not installed on Member1's Mac, so the Spring app was not run here.

## Final-validation command rehearsed — 10 October 2026

`scripts/run_validation.sh <images> <name>` (+ `ml/validate.py`). Rehearsed on 26 supplied images, 1–2 per camera, all 14 cameras, curtain and camera-reference frames excluded (mock of the 26-image validation set):
- **Camera folders:** 281 areas, complete submission, no fallbacks, **2 min 58 s end to end** (upload, prepare and inference on knuth, fetch, export); model time 151 s, 5.5 s per image. Decisions identical to the full-dataset export for all 281 areas.
- **Flat ZIP (no camera folders):** cameras inferred from the closest reference view, 25/25 correct (worst correct distance 25.9 vs nearest wrong ≥ 35.4). Two cameras share a filename timestamp, so a flat layout can collide; the real set is most likely in camera folders (annotation keys start with camera).
- **knuth unreachable:** local preparation + complete fallback submission (half, compliant everywhere) in 3 s, with `!!!` warnings. Validated coverage 281/281.
- Outputs: `data/val-<name>/` (`report.json` lists each image's camera and how it was found; `inference.log`; `export/`). Remote: `/workspace/jx/val-<name>`.

## Batch v3 labels, uncached cost, half rule v2 — 10 October 2026

- **Labels:** batch v3 frozen by Member1 (blind, no suggestions): `data/ground-truth/human-v4-frozen.json` (copy of root export `sensei-6e5566ba3be1f7ba-frozen.json`), SHA256 `252f37ff7e74…`, 98 items, all visible. Development 78 (6 empty / 12 half / 60 full, 1 mismatch); evaluation 20 (1 / 2 / 17, 2 mismatches). Labelled total now 298 observations.
- **Measured cost (uncached stock-only run over all 1,962 areas):** p50 0.550 s per area, **5.5 s per camera image** (p95 8.8 s), 18.0 min for the dataset, 55.6 GB peak. Decisions identical to the cached run (deterministic). Model time only; excludes 4.5 s model load and input preparation.
- **Half rule v1 (0.15) did not transfer:** on the 48 new development areas no rule scores 106 vs 89 with it; the rule helps only the original 29 areas (many half shelves). Validation spans all 152 areas.
- **Half rule v2 = threshold 0.20**, chosen on development (160 obs, 63 areas; best raw 201 and area-weighted 135.8 per 100 obs). Totals on stock-only answers:

| Threshold | Development | Holdout | Evaluation (90 obs) | All |
|---|---|---|---|---|
| none | 179 | 13 | 90 | 282 |
| 0.15 (v1) | 197 | 39 | 66 | 302 |
| **0.20 (v2)** | **201** | 35 | 81 | **317** |
| 0.30 | 184 | 27 | 105 | 316 |

  Evaluation has been seen before (v1 decisions), so it is not a blind test of v2. Export: `results/qwen3.8-27b-stockonly-half020-full-v1/` (130 empty / 656 half / 1,176 full; 383 decisions changed by the rule; 15 fallbacks).

## Fewer questions, SAM 3 coverage, review batch v3 — 10 October 2026

All on the 200 labelled observations (`data/labelled-v1/sample.json`, subset of the full-run inputs, built with `python3 -m ml.compare_runs --make-manifest data/full-v1/sample.json data/labelled-v1`), uncached, batch 1. Decisions made on development (v2+v3 dev), checked on holdouts; evaluation reported last. Scored with `python3 -m ml.compare_runs <results.json>…`. All variants answer compliant when compliance is not asked.

| Pipeline (+ half rule) | Dev | Holdouts | Evaluation | Total | Questions/area | p50 s/area |
|---|---|---|---|---|---|---|
| 4 questions (full-v1) | 96 | 23 | 11 | 130 | 3.74 | 1.58 |
| presence + stock | 99 | 43 | 41 | 183 | 1.87 | 0.72 |
| **stock only** | **108** | 39 | 50 | **197** | 1.00 | **0.55** |
| presence + stock, crop only | 78 | 8 | 43 | 129 | 1.87 | 0.39 |
| stock only, crop only | 67 | −6 | 54 | 115 | 1.00 | 0.20 |

- **Adopted: stock only + half rule + always compliant** (`--questions stock`). Best on development, ~3× cheaper (≈ 6 s per camera image extrapolated). Camera context matters for stock: crop-only is cheaper but clearly worse on development and holdout. Without the half rule stock-only scores 73 / 13 / 59: the rule still helps development and holdout but costs 9 points on evaluation.
- **SAM 3 coverage not adopted.** `ml/coverage.py` (English prompts in `ml/products_en.json`, union of product name + "produce" (+ "bag" if packaged) at threshold 0.3, valid pixels only): 0.13 s per crop. Median coverage by human label ≈ 0 empty / 0.45–0.55 half / 0.6–0.76 full, with overlap and some 0.0 misses on packaged full areas. On stock-only answers: "full → half if coverage < t" scored ≤ 88 on dev; "half rule only if coverage < t" ≤ 107 on dev (vs 108 without coverage) and worse on holdouts. It looked better on evaluation (59–61 vs 50) but choosing it for that would be tuning on evaluation. Files: `data/labelled-v1/coverage.json`.
- **Full stock-only export:** `results/qwen3.8-27b-stockonly-halfrule-full-v1/` (now the recommended app data; contract updated). 1,726 stock answers reused from the full-run cache, 236 new; scores identical to the labelled run (197). 15 stock fallbacks; 120 empty / 806 half / 1,036 full. An uncached full stock-only run for a clean per-image cost is running (`run-stockonly-fresh.log` on knuth).
- **Review batch v3** (blind, no suggestions): `data/human-review-v3/`, set `6e5566ba3be1f7ba`, served on port 8767. 98 crops: 78 **development** from 48 never-used areas (fresh areas go to development this time to widen tuning beyond 15 areas) + 20 new frames of evaluation areas. 13 cameras (6386 has no unused areas), 50 products, 21 packaged; no duplicates, no split changes, curtain frames excluded. Built with `python3 -m ml.label_set --expand-from data/human-review-v1 --expand-from data/human-review-v2 --labels data/ground-truth/human-v2-frozen.json --labels data/ground-truth/human-v3-frozen.json --output data/human-review-v3 --exclude-image 6383/1751001156.jpg --exclude-image 6386/1751001156.jpg --counts '{"evaluation": 20, "fresh": 80}' --fresh-split development`. The generalised selection reproduces v2 exactly.

## Full Sensei export (Qwen3.8-27B, prompt v1, half rule) — 10 October 2026

- **Run:** all 181 images / 1,962 areas on knuth (`/workspace/jx/sensei-full-v1`, `run.sh`, `run.log`); `ml/export.py inputs` then `ml.infer_sample --stock-prompt v1`, batch 1, bf16, model preloaded (load 4.5 s). Local copy: `data/full-v1/{sample,results,answers}.json`.
- **Export:** `python3 -m ml.export outputs data/full-v1/results.json --output data/full-v1/export --run-id qwen3.8-27b-v1-halfrule-full-v1` → `submission.json` (exact Sensei format, validated: all 1,962 keys, consistent level/value), `snapshots.json` (contract app records, `prediction_source: saved`), `report.json`. Fallbacks (half / compliant) used for 41 stock and 186 compliance answers; half rule changed 449 stock decisions. Output: 247 empty / 738 half / 977 full; 250 non-compliant.
- **Measured processing cost (model time only):** median **16.0 s per camera image** (p95 25.0 s; 10.8 areas/image), 2,925 s for 181 images, 56 GB GPU memory on one RTX PRO 6000 Blackwell. Not included: model load (4.5 s once) and input preparation (~20 min CPU for 1,962 outlined context JPEGs, avoidable). At a hypothetical rate R per GPU-hour: ≈ 0.0044 R per image. No real tariff known.
- **Scored against all human labels (same run):** reproduces earlier dev numbers exactly (16/55 → 40/55 with rule).

| Policy | v2 dev | v2 hold | v3 dev | v3 hold | v3 evaluation (fresh areas) | Total |
|---|---|---|---|---|---|---|
| model | 16/55 | −5/44 | 49/100 | −4/40 | 19/140 | 75 |
| model + half rule (**exported**) | 40/55 | 10/44 | 56/100 | 13/40 | 11/140 | 130 |
| model + half rule, always compliant | 40/55 | 16/44 | 56/100 | 19/40 | 41/140 | 172 |
| constant full, compliant | −17/55 | −20/44 | 36/100 | 4/40 | 34/140 | 37 |

- **On the 70 fresh evaluation areas the exported pipeline loses to the constant "full + compliant" (11 vs 34).** Causes: compliance false alarms (13 of 64 compliant flagged; only 3 of 6 real mismatches caught) and the half rule turning true full into half (5 → 14 errors) on areas that are mostly full (48/70). The half rule still helps on dev/holdout areas.
- "Always compliant" is best on every group, but it was identified after seeing the evaluation results (no longer a clean test for that choice) and gives up mismatch detection. Decision pending.

## Human review set v2 (140 more crops) — 10 October 2026

Versioned expansion to bring reviewed observations to 200. `data/human-review-v1/`, the 60 frozen labels, their browser storage and all cached predictions are untouched.

- **Set:** `data/human-review-v2/`, set ID `9fd095a34a5b339b`, protocol `sensei-box-capacity-v3` (separate browser storage key). Built by `python3 -m ml.label_set --expand-from data/human-review-v1 --output data/human-review-v2 --exclude-image 6383/1751001156.jpg --exclude-image 6386/1751001156.jpg` (refuses to overwrite).
- **Selection (deterministic):** no observation from v1. Areas keep their v1 split; areas used in any experiment (`data/*/sample.json`, e.g. `6215_2`) are development; never-used areas form the new **evaluation** group, not selected from model errors. Development +50 (frames of the 15 development areas, spread over the day), holdout +20 (14 holdout areas), evaluation 70 (69 never-used areas, 5 per camera, packaged products first, start times rotated across the day; 6386 has only 4 unused areas so one gets 2 frames). All 14 cameras, 72 products, 47 packaged items, captures 06:00–18:00 UTC.
- **Exclusions:** the only closed-curtain frames are the first images of the day on 6383 and 6386 (`1751001156.jpg`, checked on all 13 frames of each camera; matches the 4 frozen blocked labels). White packaging and empty trays are kept.
- **Assistant suggestions:** `suggestions.json`, source `assistant_visual_review_v3`, `confirmed: false`. Every crop was inspected with its outlined context. 90 full / 36 half / 13 empty / 1 stock uncertain; 52 flagged uncertain with candidate levels; 4 with uncertain product match (narrow packaged targets on 6376/6443). Two real wrong-product candidates: #74 `6215_9` (bananas where oranges are planned) and #131 `6594_2` (apparent onions in nets where 5 kg red potato bags are planned). Suggestions follow the v3 rules (polygon only, capacity-relative, empty includes nearly depleted, empty area compliant); no prediction threshold, probabilities or penalties were used.
- **Page:** shows crop, outlined context, expected product, split, suggestion with reason and flag, and read-only frozen v1 labels for the same area at other times. No model predictions. Saved human answers override suggestions; browsing never saves (leaving an edited example asks to discard); only Save & next confirms. Progress, "Only flagged / uncertain" filter, browser persistence, draft export (saved answers only, suggestions kept separately), freeze/export after all 140.
- **Tests:** 19 headless-Chrome checks passed (save/advance, provenance, discard dialog, human priority, reload persistence, uncertainty filter, draft/frozen export contents, freeze lock, v1 storage untouched, no page errors); test profile was temporary, not the user's browser. Python selection test added to the smoke test.
- **Open:** `python3 -m http.server 8766 --bind 127.0.0.1 --directory data/human-review-v2`, then `http://127.0.0.1:8766`. Keep using port 8766 for v2 (storage is per port).
- **Labels collected (Member1, all 140, protocol v3):** the Export button did nothing because the Reviewer field was empty (the message was easy to miss; now an alert + focus). Labels were recovered from browser storage via console into `data/ground-truth/human-v3-browser-backup.json` (raw, preserved) and rebuilt as `data/ground-truth/human-v3-frozen.json` in the page's frozen format, with `frozen_from` provenance; SHA256 `952fc2b5…bd6b`. Assisted, not blind.
  - Development 50: 4 empty / 12 half / 34 full, no mismatch. Holdout 20: 1 / 8 / 11, no mismatch. Evaluation 70: 7 / 15 / 48, **6 wrong-product labels** (`6215_9` oranges planned, bananas visible; three narrow `6376` packaged areas; `6443_3`; `6594_2`). First real non-compliant labels we have.
  - The reviewer changed 18 stock and 5 compliance suggestions (22 items).
- **Scoring:** `ml/evaluate_review.py` now takes the protocol revision from the set manifest and accepts `--split evaluation`; use `--review-dir data/human-review-v2` with the v3 labels. Keep evaluation for final checks, not tuning.

## Fixed half rule, holdout test — 10 October 2026

Rule (locked in `ml/decision_rule.py`, commit `97bfa39`, before the holdout run): when a stock answer exists and its B score ≥ 0.15, predict `half`; every other decision and fallback unchanged. Threshold chosen in-sample on development; applied **once** to the cached Qwen3.8-27B v1 holdout outputs; no threshold search afterwards. No GPU, prompts or labels changed.

| Split | Before | With rule | Stock | Stock points | Best constant |
|---|---|---|---|---|---|
| Development (tuned here) | 16/55 | **40/55** | 20/30 → 26/30 | −9 → +15 | half −1/55 |
| Holdout (rule fixed beforehand) | −5/44 | **10/44** | 15/26 → 18/26 | −17 → −2 | half −6/44 |

- Holdout confusion: true half → full drops 8 → 2 (half correct 3 → 9); new cost is 3 true-full areas now predicted half (−2 each). Empty and compliance decisions unchanged (16/18; 2 stock / 1 compliance fallbacks as before).
- The gain holds out of sample (+15 points on holdout vs +24 in-sample), but the holdout was inspected earlier: useful validation of a fixed rule, not a pristine blind test. 26 stock labels, assisted annotation.
- This is a **label-tuned decision rule**, not evidence that scores are calibrated probabilities. Describe it that way; ask the mentor about label-tuned thresholds if needed.
- Processing cost: negligible (post-processing of existing scores).

Files: `data/eval-half-rule-v1/{dev,holdout}-{results,metrics}.json` (local, ignored). Reproduce: `python3 -m ml.decision_rule data/eval-holdout-v1/results.json --output <new>.json`, then `python3 -m ml.evaluate_review score data/ground-truth/human-v2-frozen.json --split holdout --predictions <new>.json --output <new-metrics>.json`.

## Dev error review, stock prompt v2, smaller VLM — 10 October 2026

Development split only (32 items, 30 stock / 25 compliance labels; frozen GT unchanged). Holdout not used. Inputs copied to `data/eval-dev-stock-v2/` (originals in `data/eval-dev-v1/` untouched); remote `/workspace/jx/sensei-dev-stock-v2` (`run27b.sh`, `run4b.sh`, `runprefix.sh` + logs). Batch size 1, model preloaded, timings exclude load.

**Error review (assistant, from crops + labels; no user notes exported):** all 10 errors are stock on true-half areas: 9 predicted full, 1 (squash `6594_1751001189`) predicted empty. Every half→full case shows visible bare floor/empty cells with many items left (apple trays with empty cups, teal floor between lemons/potatoes, basket weave under peppers/cabbage, cardboard around strawberries). Over-estimation costs −3 each, so these 9 cost 27 of the stock points. Compliance had no errors (all labels positive, still untested on real mismatches).

| Run | Points | Stock | Fallbacks (stock/compl.) | Questions | p50 s/area | Total s | Peak GB |
|---|---|---|---|---|---|---|---|
| Qwen3.8-27B, prompt v1 (replay, current code) | 16/55 | 20/30 | 0/0 | 114 (17 cached) | 1.39 | 37.9 | 55.6 |
| Qwen3.8-27B, stock prompt v2 (no cache) | 15/55 | 20/30 | 0/0 | 114 | 1.46 | 42.7 | 55.7 |
| Qwen3.8-27B, v1 + `--answer-prefix "Answer: "` | 18/55 | 20/30 | 2/2 | 108 | 1.42 | 40.1 | 55.6 |
| Qwen3.5-4B, v1 (no prefix) | −1/55 | 13/30 | 30/25 | 45 | 0.17 | 6.9 | 9.8 |
| Qwen3.5-4B, v1 + answer prefix | 0/55 | 13/30 | 0/0 | 114 | 0.46 | 14.1 | 9.8 |
| Best constant (half) | −1/55 | 13/30 | — | — | — | — | — |

- **Stock prompt v2 rejected.** v2 defines levels by bare floor/empty cells. It fixed the squash (empty→half) but broke one lemon tray (half→full) and pushed almost every full score to ~1.00: the model does not act on the floor criterion. `--stock-prompt v1` stays the default. Cached vs uncached v2 runs gave identical decisions.
- **Qwen3.5-4B rejected for scoring.** Without a prefix it starts with "Based on…"/"To determine…", so A/B/C held as little as 5% of next-token mass and every item fell back (= half baseline). With `--answer-prefix "Answer: "` mass ≥ 0.89, no fallbacks, ~3× faster and 5.7× less memory, but stock collapses to 13/30 (9 true-half → empty), 0/55: no better than the constant baseline.
- **Answer prefix on 27B: not adopted.** +2 points but it introduced 2 fallbacks (letter mass ≈ 0 on those questions); the gain is within noise and partly from fallbacks.
- **Rough cost per camera image** (serial extrapolation, 10.84 areas/image, not a full-frame measurement): 27B ≈ 15 s, 4B ≈ 5 s.

**Lead for the next experiment (in-sample, not a result):** on the v1 replay, predicting half whenever the stock B score ≥ 0.15 would move dev stock from 20/30 (−9 points) to 26/30 (+15). This threshold was chosen on the same 25 items, so it must be tested on data it was not tuned on (e.g. existing cached holdout answers, no GPU) under a declared protocol, and it is a form of calibration on hand labels (see PLAN mentor question).

Code: `ml/infer_sample.py` adds `--stock-prompt {v1,v2}` (default v1, old cache keys unchanged) and `--answer-prefix` (included in cache keys). knuth: added `/workspace/models/qwen3.5-4b` (9.3 GB); 28 GB free.

## Latest evaluation and agent handoff — 10 October 2026

**Use this section as current state; older sections below are experiment history, not current results.** User supplied frozen, human-reviewed local GT. The revised model was evaluated against it, with closed curtains excluded. No further prompt changes were made between development and holdout runs.

| Split | Stock accuracy | Compliance agreement | Local task points | Best constant baseline |
|---|---|---|---|---|
| Development | 20/30 (66.7%) | 25/25 (100%) | 16/55 | half: -1/55 |
| Holdout | 15/26 (57.7%) | 16/18 (88.9%) | -5/44 | half: -6/44 |

Points use Sensei's per-task penalties but only definite local labels, so maximum equals eligible stock labels plus eligible compliance labels. These are NOT the official 289-area score. All definite compliance labels in both splits are true: this reference cannot measure real wrong-product recall. Holdout gain is only one point over the half baseline, not convincing evidence of reliable generalisation. Labels were assistant-prefilled and human-reviewed, not independently blinded.

Exclusions: exactly two human-labelled curtain observations in each split; no stock/product points from them. Uncertain compliance is also excluded independently (five additional visible development cases, eight additional visible holdout cases). Stock has 30/26 eligible labels. Coverage is checked before exclusions; missing prediction records fail evaluation. Predicted abstentions on visible labelled cases are scored with fixed half/true fallbacks and counted, never silently excluded. Development: no fallbacks. Holdout: two stock fallbacks, one eligible compliance fallback.

Development stock confusion (truth → prediction): empty 5 empty; half 1 empty / 3 half / 9 full; full 12 full. Holdout: empty 3 empty / 2 half; half 3 half / 8 full; full 1 empty / 9 full. Primary issue is half→full overestimation. Holdout also exposes two visible empty trays rejected by the visibility stage. Since validation is guaranteed visible, a validation-only bypass is a sensible next controlled experiment; preserve optional visibility handling for arbitrary demo inputs. Do not reinterpret these exposed holdout cases as a fresh test set for further tuning.

### Files and provenance

- Original user export: `sensei-93b9d1c2db63ec53-frozen.json` at repo root (untracked; preserve it).
- Working GT: `data/ground-truth/human-v2-frozen.json`; 60 items, reviewer Member1, all `sensei-box-capacity-v2`, frozen at `2026-10-10T14:31:37.406Z`.
- GT SHA256: `1370063e9cb7c7308b92a7933c3b07031abccc644135d1cae6b75c6da5508ab3`.
- Fixed image set: `data/human-review-v1/manifest.json`; set `93b9d1c2db63ec53`; 32 development / 28 area-disjoint holdout. Local browser labeling remains available at port 8765. Suggestions v1/v2 and saved labels must not be regenerated or overwritten.
- Model predictions: `data/eval-dev-v1/results.json`, `data/eval-holdout-v1/results.json`.
- Reproducible metrics including error IDs, confusion matrices, baselines and input hashes: corresponding `metrics.json` files.
- Prepared inference inputs: corresponding `sample.json` and images/masks. No GT fields are present in these manifests.
- Local development `answers.json` contains seeds; remote run caches contain newly computed answers too. The prediction records preserve cache-hit flags. Reuse individual question answers only for identical model/prompt/image bytes and unchanged inference environment.
- Actual model: `/workspace/models/qwen3.8-27b`; Python: `/workspace/miniconda/envs/jx/bin/python`. Remote directories: `/workspace/jx/sensei-eval-dev-v1` and `/workspace/jx/sensei-eval-holdout-v1`, with `run.log`, source runner and `data/` outputs. Both runs finished. No packages, model files or unrelated processes changed.
- Source implementation: `ml/infer_sample.py`, `ml/evaluate_review.py`; tests `ml/test_infer_sample.py`, `ml/test_evaluate_review.py`; full smoke `bash scripts/smoke_test.sh` (11 test methods).

### Reproduction commands

From repository root; choose new output names because preparation and scoring refuse overwriting prior results:
```bash
python3 -m ml.evaluate_review prepare data/ground-truth/human-v2-frozen.json --split development --output data/eval-dev-next
python3 -m ml.evaluate_review score data/ground-truth/human-v2-frozen.json --split development --predictions data/eval-dev-v1/results.json --output data/eval-dev-v1/metrics-check.json
python3 -m ml.evaluate_review score data/ground-truth/human-v2-frozen.json --split holdout --predictions data/eval-holdout-v1/results.json --output data/eval-holdout-v1/metrics-check.json
```
For inference, copy the chosen input directory and runner to a new directory below `/workspace/jx` on knuth. From that remote directory:
```bash
/workspace/miniconda/envs/jx/bin/python -B -u -m ml.infer_sample data/eval-dev-v1/sample.json --model /workspace/models/qwen3.8-27b --output data/eval-dev-v1/results.json --answer-cache data/eval-dev-v1/answers.json
```
Use the matching `eval-holdout-v1` paths for the existing holdout run. Existing completed results return from cache; changed code/input settings require a new result file. Do not rerun unchanged GPU questions. Copy result/cache JSON back locally before scoring. Never send ground truth into inference prompts.

Timing: development processing total 37.87 s with 17 cached questions; holdout total 34.37 s, no cached questions, median 1.40 s/example, excluding model load, transfer and preparation. These are small-sample measurements, not public-app latency or a measured full-dataset run.

### Next agent's priorities

1. Work only against development labels for tuning; inspect half→full errors. Stock question now allows A empty / B half / C full / D uncertain even when produce is visible. Product capacity and supplied-polygon semantics are explicit. Scores are uncalibrated: do not apply expected-payoff optimisation as if they were calibrated probabilities.
2. Evaluate a validation-visible path without the visibility gate; include all required prediction keys and disclose fallback policy. Do not spend time on closed-curtain accuracy.
3. Finish official-format and app snapshot export from actual model predictions. Current `results.json` is diagnostic, NOT submission format; `data/prepared-v1/snapshots.json` is still the disclosed constant fallback.
4. Run all 1,962 observations only after export/schema checks and a small measured comparison. Connect API/UI and rehearse the demo. No API/UI, public deployment or complete full-dataset model export was verified here.
5. Keep current labels frozen; any correction requires an explicit new version. Human assisted labels, small sample size, absent negative compliance cases and exposed holdout constrain claims. Preserve files under ignored `data/`; a fresh clone alone is insufficient to reproduce this run.

## Dataset inspection — 10 October 2026

Source: local `new_dataset_hackathon_junctionx_10_oct_2026_v2/`, containing the challenge PDF, `planogram.json` and the train/test image ZIP. No ground-truth annotation file is present in the supplied directory or ZIP; the planogram specifies expected products and geometry, not per-image labels. No explicit train/test subdivision appears inside the ZIP.

| Measurement | Observed |
|---|---|
| Images / dimensions | 181 / all 1280 × 720; all decoded successfully |
| Cameras / planogram areas / product IDs | 14 / 152 / 94 |
| Required area observations in supplied images | 1,962 (not the hidden validation set's 289) |
| Images per camera | 12–14 |
| Filename timestamp range | 27 June 2025, 05:12:35–19:16:54 UTC |
| Consecutive same-camera gaps | 3,604–4,696 seconds, approximately 60–78 minutes |
| Rectified crop dimensions | Width 44–293 px; height 78–213 px |
| Partly off-image areas | `6383_5`, `6383_6`, `6383_7`, `6386_3`, `6386_4`; approximately 63–75% valid pixels |

Visual inspection: early images on 6383/6386 show closed white refrigeration curtains; middle/later examples show the shelves uncovered. A closed curtain conceals stock and is not evidence of an empty shelf. Early frames on other cameras also show sparsely stocked/empty areas. Original images include strong crate colours, shelf labels, packaged and loose produce.

Consequence: remove short-window temporal imputation from the current-data baseline; an hour-old frame can span a restock. No depletion-rate/time-to-empty claim is justified. Start with current-image inference and explicitly handle visibility. Reference experiments remain optional and require evaluation.

## Metrics

No accuracy or official score measured. Generated all three constant-stock/compliant baselines with complete 1,962-area coverage. App records currently expose the half baseline as a disclosed fallback with unknown visibility; they are not image classifications.

Six synthetic test methods pass, covering the nine stock payoff combinations, compliance penalties, missing-area penalty, expected-score choice, strict value/coverage checks, off-image masks, crop orientation, malformed geometry, ZIP metadata handling, preservation of prior output directories single-token answer encoding checks and staged early exits.

## How measured

- ZIP inventory and Pillow decoding; image filename timestamps and planogram counts.
- `python3 -m ml.prepare new_dataset_hackathon_junctionx_10_oct_2026_v2 --output data/prepared-v1` completed on all images.
- Inspected a 14-camera overview, first/middle/last frames on both curtain cameras, and selected crops with masks. Not every crop has been visually reviewed.
- `bash scripts/smoke_test.sh` runs the synthetic preparation/scoring checks. GPU inference and API/UI have not been tested by this command.

## Qwen diagnostic sample — 10 October 2026

Ran `/workspace/models/qwen3.8-27b` on knuth over 12 area observations from 6 cameras. Each question received the full camera image with the target outlined in red and its rectified crop. Three separate A/B/C questions covered visibility, stock and product-type compliance. This is a diagnostic sample, not a labelled benchmark; no official score or accuracy is available.

- Model load: 4.57 seconds; median processing: 1.405 seconds per area for all three questions; first area: 2.14 seconds. Peak PyTorch allocated memory: 55.52 GB (decimal, not total GPU usage).
- Both selected closed white curtains were classified as obstructed. Their stock answers were nevertheless empty: visibility must gate downstream actions; never turn those raw stock answers into restock alerts.
- A visible cabbage tray (`6386/1751024835.jpg/6386_3`) was incorrectly classified as obstructed, apparently sensitive to the frame/padding or partial obstruction. The cause needs checking.
- A sparsely stocked banana tray (`6215/1751001268.jpg/6215_1`) was called empty despite visible bananas. This contradicts the diagnostic prompt's literal no-produce definition; the official empty/half boundary remains unconfirmed.
- Fully empty banana/pineapple trays were called empty; populated watermelon, pepper and onion examples were called full. These are qualitative observations, not verified official labels. The sample contains no verified wrong-product example, so mismatch detection is untested.
- Allowed answer tokens accounted for at least 99.85% of next-token probability mass. Normalised answer scores remain **uncalibrated** and must not be displayed as accuracy or used to claim calibrated cost optimisation.

Implementation: `ml/infer_sample.py`; rejects conflicting cached inputs/settings and saves after every area. Manifest entries contain `sample_id`, `product_name`, `context` and `crop` filenames relative to the manifest. Local inputs/cache: `data/qwen-sample-v1/{sample,results}.json`. Remote workspace: `/workspace/jx/sensei-sample-v1`. No packages or models were installed/downloaded. Existing PyTorch fallback kernels emitted performance warnings; no environment changes were made.

Historical v1 reproduction uses the preserved runner in that remote workspace (the current runner requires a mask):
```bash
/workspace/miniconda/envs/jx/bin/python -B -u -m ml.infer_sample data/qwen-sample-v1/sample.json --model /workspace/models/qwen3.8-27b --output data/qwen-sample-v1/results.json
```
Unchanged completed samples return from cache without loading the model. Use a different output filename for a deliberately changed prompt/model experiment.

Next: clarify empty/half and curtain annotation rules; compare a revised visibility/stock prompt on these failure cases plus unchanged controls. Add a verified mismatch case before trusting compliance. At this sample speed, 1,962 areas would take roughly 46 minutes, excluding transfer/preparation and variation in image processing; do not spend that run before checking the failure cases. API/UI and the full-dataset inference/export path remain untested.


## Staged diagnostic v2 — 10 October 2026

Same 12 observations, same model, new prompts plus a third image containing the aligned validity mask. Expected product is supplied only for the compliance question. Code gates stages: blocked/unknown visibility skips all other questions; clear views get a presence question; empty/unknown presence skips stock/compliance. Visible produce gets half/full/unknown and match/mismatch/unknown questions. Null observations are diagnostic abstentions, not valid Sensei export fields. No app snapshot or baseline files were overwritten.

- Both closed curtains stop after visibility, with `action: inspect` and no stock/compliance observation.
- The open cabbage tray is now clear, full and matching. Because prompts and mask input changed together, this does not isolate which change fixed it.
- Sparse bananas remain incorrectly classified as absent. Do not claim this failure is fixed or publish these diagnostic actions as validated alerts.
- Median time: 1.956 seconds/area; blocked examples: approximately 0.50 seconds; populated examples: approximately 1.95–2.00 seconds. Peak PyTorch allocated memory: 55.60 GB. Total questions: 36 (same as v1, redistributed by gating). A mostly visible full run may take about 65 minutes; reserve time, but first isolate the sparse-produce error on a smaller sample.
- Six synthetic test methods pass, including exact early-exit call sequences, empty/unknown abstention and populated-tray actions. Verified a repeated run uses cache without loading the model.

Inputs/results: `data/qwen-sample-v2/{sample,results}.json`; manifest adds `mask`, a filename relative to the manifest. Remote workspace: `/workspace/jx/sensei-staged-v2`. From that workspace:
```bash
/workspace/miniconda/envs/jx/bin/python -B -u -m ml.infer_sample data/qwen-sample-v2/sample.json --model /workspace/models/qwen3.8-27b --output data/qwen-sample-v2/results.json
```

No official labels, accuracy, calibration or verified mismatch test. The selected development cases are not a held-out evaluation. Next experiment should compare tight-crop-only presence against context-plus-crop on the sparse banana case and controls, keeping the same model; do not add another perception model before checking whether context is distracting it.


## Presence input comparison — 10 October 2026

Compared cached v2 presence answers with a new crop-plus-mask-only presence query on its ten clear-view examples. Same Qwen model, same crop/mask pixels, same presence question and answer scoring; removed the full-camera image and adjusted the image-description prefix accordingly. Closed curtains were excluded using cached visibility. No previous inference was rerun.

- Sparse banana case `6215/1751001268.jpg/6215_1`: changed from absent to present, agreeing with visual inspection. The A/B/C scores were 0.845/0.130/0.026, uncalibrated.
- All nine other presence decisions stayed unchanged: seven populated examples stayed present and two visibly empty trays stayed absent. This is a development-case comparison, not official accuracy or a held-out benchmark.
- Median presence-query time: 0.180 seconds; first query: approximately 0.95 seconds. These are single-question timings, not whole-area pipeline latency.
- The change supports removing camera context for presence, but does not prove the causal mechanism or generalisation. Processor image allocation also changes when an image is removed.

Runner option: `--crop-presence-only`. It deliberately produces only presence answers and no stock, compliance or staff actions; the default staged runner remains unchanged. Inputs/results: `data/qwen-presence-ablation/{sample,results}.json`. Remote workspace: `/workspace/jx/sensei-presence-ablation`.
```bash
/workspace/miniconda/envs/jx/bin/python -B -u -m ml.infer_sample data/qwen-presence-ablation/sample.json --model /workspace/models/qwen3.8-27b --output data/qwen-presence-ablation/results.json --crop-presence-only
```
Verified all ten outputs contain only presence, exactly one answer changed, both empty controls remain absent, and repeated execution uses cache without loading the model. Seven synthetic test methods now pass, including the diagnostic CLI's empty-input and missing-mask handling.

Next: integrate crop-plus-mask presence into the visibility-gated flow, then assess stock/compliance for the newly admitted sparse case and check fresh examples before broad inference. Do not claim stock classification is fixed: this experiment tested only presence.


## Integrated crop-presence pipeline — 10 October 2026

Default staged inference now uses crop+mask for presence while retaining context+crop+mask for visibility, fill and compliance. Tested 20 observations across all 14 cameras: previous 12 cases plus one mid-day first-area observation from each of eight previously unseen cameras. This sample was chosen for coverage, not class balance.

- Reused 36 identical question answers from v2 and the presence comparison; ran only 34 new questions. Per-question cache keys include model path, exact prompt and ordered image bytes. Keep model contents/environment fixed when reusing this cache; use a separate cache after replacing model weights or changing inference settings.
- Sparse bananas now pass presence and are classified half; product match is uncertain, so the diagnostic action is inspect. Both closed curtains still stop after visibility; the open cabbage tray remains inspectable.
- All eight added crops are classified visible and populated, consistent with provisional visual inspection. Stock agrees with six non-ambiguous provisional visual judgments; lemons and potatoes remain ambiguous half/full cases and were not assigned a reference level.
- Product identification is now the main observed weakness: both new apple examples and the packaged strawberry example receive mismatch answers despite visually plausible product-type matches. Apricot identity is uncertain on visual review. These are suspected false alarms, not authoritative cultivar/brand labels.
- New complete four-stage examples took approximately 1.68–1.71 seconds each; cached examples' near-zero times are cache retrieval, not inference throughput.

Inputs/results: `data/qwen-integrated-v3/{sample,results}.json`; the per-question seed cache is `answers.json`. Provisional visual review: `visual-review.json`, authored by the assistant, not a human or Sensei, covering eight new cases plus sparse bananas. These checks are for development, not supervised training/calibration. The eight new crops were reviewed before reading their model outputs. A team member should review uncertain labels; never silently turn these into official truth.

Remote workspace: `/workspace/jx/sensei-integrated-v3`:
```bash
/workspace/miniconda/envs/jx/bin/python -B -u -m ml.infer_sample data/qwen-integrated-v3/sample.json --model /workspace/models/qwen3.8-27b --output data/qwen-integrated-v3/results.json --answer-cache data/qwen-integrated-v3/answers.json
```

Eight synthetic test methods pass, including input selection, expected-product isolation and cache identity. API/UI and full-dataset submission remain separate unfinished steps. Next: isolate product-match false alarms using the same input-comparison approach, preserving visibility gates and cached answers.

Clarification from the supplied brief: shared train/test images have no annotations; only the hidden final validation has `annotations.json`. The JSON shown in the PDF illustrates its format, not labels for all supplied images. We are not waiting for more labels: proceed with the planogram, image inspection and a small provisional development reference set. The final competition score will come from Sensei at the end as planned.


## Crop-only product matching and integration — 10 October 2026

Ran 16 visible/populated cases using crop+mask for compliance, keeping the question and expected product unchanged and removing camera context. Compared with cached v3 answers. Added four explicitly synthetic wrong-product expectations (banana→tomato, tomato→banana, lemon→strawberry, cabbage→lemon) to test obvious rejection; these are not real shelf mismatches.

All 16 actual expected-product queries returned match. The two apple examples and packaged strawberry example no longer trigger the suspected false alarms; sparse bananas move from uncertain to match. Apricot also moves from mismatch to match, but its exact identity remains unverified by a human. All four synthetic wrong expectations returned mismatch. This is a development comparison, not a claim of 100% real-world compliance accuracy; subtle cultivar and mixed-product errors are still untested.

Default pipeline now uses crop+mask for both presence and compliance, with camera context retained for visibility and stock. Integrated all 20 original examples by replaying exact prompt/image cache matches through the stage logic, without repeating inference. The sparse banana tray now yields half/match and `check_stock`; both curtains still yield `inspect`. Eight synthetic test methods pass.

Experiment inputs/results: `data/qwen-compliance-ablation/{sample,results}.json`; remote workspace `/workspace/jx/sensei-compliance-ablation`. Diagnostic flag: `--crop-compliance-only` (mutually exclusive with `--crop-presence-only`). Integrated cached replay: `data/qwen-integrated-v4/replay-results.json`, with input manifest and seeded question cache alongside it. This replay is a diagnostic artifact, not the competition export or app snapshots. No new live end-to-end latency measurement was made for the final combination.

Next delivery: complete scoring/app exports with explicit fallbacks for unobservable cases, then broader visual review and a full dataset run. Keep ambiguous half/full examples uncertain in development references. No dependence on receiving training labels; final scoring follows Sensei's end-of-event validation.


## Human review set v1 — 10 October 2026

Built `data/human-review-v1/`: 60 observations, 32 development and 28 held-out, spanning all 14 cameras. Each camera contributes first/last frames of one development area and one previously untested area; four development areas also contribute middle frames. Splits are area-disjoint. Held-out areas exclude every area in the existing `data/qwen*/sample.json` manifests at creation. This is a coverage-oriented sample, not a random estimate of production accuracy; it does not deliberately include verified real mismatches.

Set ID: `93b9d1c2db63ec53`. The manifest fixes image/crop hashes, sampling split and provisional labeling definitions. Generated artifacts stay local. No model answers are shown or prefilled. Human labels have **not** been collected yet. Stock choices are empty/half/full or uncertain; blocked observations and empty-area compliance remain null for local review, not fabricated competition labels. Product labels refer to visibly identifiable type, not unverifiable cultivar/brand/origin.

Build with `python3 -m ml.label_set --output data/human-review-v1` (refuses overwriting an existing set). Open via `python3 -m http.server 8765 --bind 127.0.0.1 --directory data/human-review-v1`, then visit `http://127.0.0.1:8765`. Enter reviewer, label each item, and Save & next. Draft JSON exports provide backups; freeze/export becomes available when all items are reviewed. Frozen references are locked in that browser and any later corrections must be a separate explicit revision. Save downloaded labels under the local review directory before scoring. Browser storage is local to that browser/origin; use the same browser and port when resuming.

Keep holdout results out of prompt tuning; compare development results first. Score stock and compliance separately on definite labels and report the number excluded as uncertain. Do not use partially labelled references as an official competition score. Review is for evaluation, not fine-tuning or fitting a calibration model.

Nine Python test methods pass, including deterministic area-disjoint sampling and exclusion of exposed areas. Browser checks cover blank initial answers, blocked-view gating, save/reload, null export values and mobile layout. Synthetic browser test labels are isolated and are not part of the review dataset.


## Confirmed evaluation scope — 10 October 2026

User relayed organiser guidance: create our own empty/half/full annotations; closed-white-curtain images should be discarded from task evaluation because the final validation will show products unobstructed. No additional training labels are expected. This resolves the earlier uncertainty about including curtained shelves in the benchmark.

Preserve the in-progress review set and browser labels. Mark confirmed curtain examples Blocked / curtain; their stock and compliance remain null, and they must be excluded from stock/product metric denominators and any calibration, with exclusion counts reported. Retain images as provenance/optional robustness examples rather than deleting source data. No automatic broad white-colour filter: packaging and pale shelves are valid inputs. Final submission still requires every requested area, including fallback predictions if the visibility model is mistaken.

Knuth use is authorised for the project. No server environment or hosting changes were made in this update. Next priority is collecting the human stock reference and testing visible-shelf errors, not further curtain tuning.


## Assisted annotation — 10 October 2026

At the user's request, visually inspected all 60 review-set crops and created local `data/human-review-v1/suggestions.json`: 60 assistant-authored suggestions, 4 blocked curtains, 22 attention flags. These are not Qwen outputs or confirmed human labels. Suggestions include visibility, stock, product match, reasons and candidate stock classes where ambiguous. Existing manifest/set ID and saved browser reviews are preserved. Browser-saved human answers override suggestions. Navigation alone does not confirm a suggestion; Save & next does. Exports retain suggestion provenance separately from the human review. This supersedes the earlier prediction-blind review procedure: assisted labels can introduce anchoring bias. Holdout area separation remains, but this is no longer blind human annotation.

Sensei advice relayed by the user is to choose predictions by points gained/lost. Under a hypothetical 50/50 empty/half belief, expected stock score is -0.5 for predicting empty versus -1 for half. This supports a conservative submission choice; it does not establish the true stock class or those probabilities. Three sparse examples (1, 4, 8) have tentative empty suggestions with explicit empty/half uncertainty, despite visible produce. The reviewer should resolve or retain uncertainty rather than treating cost-aware guesses as definite evaluation truth. No empirical confidence probabilities were assigned.

The labeling UI allows product match independently of stock level for visible views, so a conservative empty choice with a few visible products need not erase product identity. Genuinely empty or blocked areas still use unknown product match. Suggestions remain excluded from completed-label counts until explicitly saved. Reviewers may choose uncertain instead of the suggested class. No model fitting or evaluation against these unconfirmed suggestions was performed.


## Annotation revision v2: box and product capacity — 10 October 2026

User relayed Sensei clarification: evaluate only the provided polygon. Four watermelons filling that polygon count as full regardless of unused space outside it. Stock is relative to product capacity: two large fruits in a roughly six-fruit capacity can count as half; two small lemons in a much larger lemon capacity can count as empty. Therefore empty is not restricted to literal zero produce. Exact universal thresholds were not provided.

Reconsidered all 60 visual suggestions under this rule. Examples 4 (sparse bananas) and 8 (one large melon) change empty→half; examples 5/6 remain full within the watermelon polygons. Other suggested classes remain, with rewritten capacity-based explanations. Four curtain observations remain excluded. Removed all hypothetical 50/50-payoff justifications from active suggestion notes; class annotation and prediction payoff optimisation remain separate. Near-empty bananas in example 1 remain a tentative empty/half boundary case, not a known official label.

Local suggestions updated in `data/human-review-v1/suggestions.json`; old suggestions preserved as `suggestions-v1.json`. Image membership and split are unchanged. UI protocol revision `sensei-box-capacity-v2` uses a separate browser storage key and imports prior labels without overwriting the previous storage. Earlier labels remain visible and must be resaved under the revised protocol. A Use revised suggestion button loads the new proposal; it does not confirm it. Exports state the revised rule and revision on each confirmed label.

Existing VLM stock prompts still use the earlier presence/fill semantics; these must be aligned with the clarified near-empty definition before the next benchmark. No model was rerun or trained during this annotation revision.


## Last-session state for the next agent

User authorised further work but requested prioritising documentation before agent credits run out. Completed: empty-area compliance rule in code and its regression assertion; generated local development error review at `data/human-review-v1/errors.html` (10 errors, notes export, no GT changes); researched official small-VLM model cards and standard YOLO class scope; read-only knuth inventory. GPU was idle at inspection. No models downloaded, packages installed, GPU benchmark rerun, or ground-truth labels changed in this session.

The error-review page is a generated local artifact and not in Git. Labels, images, cached outputs and review pages live in ignored `data/`; original user frozen JSON remains untracked at repo root. Switching agents in this workspace preserves them; a new clone alone does not. Existing local annotation HTTP server is on port 8765; restart command is in the handoff above. Save user-exported error notes in `data/` and record their path before prompt changes.
