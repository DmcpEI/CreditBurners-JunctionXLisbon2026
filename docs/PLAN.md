# Plan — Sensei: Fresh eyes on fresh produce

Challenge: Sensei. Switch to QuantumTrace (Inspiring Solutions) only for a fundamental blocker (data unusable, crops unreadable, validation unavailable), not for "no edge yet". Otherwise cut scope.

## Objective
> Every area calibrates itself against its own day, and every answer is the one that costs staff least.

Two prizes, two targets, planned from hour 0:
- **Sensei prize** = automatic score on 289 hidden validation areas (max 578). Owned by `ml/`.
- **General / Peer prize** = demo and pitch. Owned by `api/` + `ui/`. Last year's winner (Forest Guardian) wrapped a known model (YOLOv8-seg) in an immediately understandable result: image → visible detection → useful action. Copy that clarity, not their stack. Ours: **shelf image → priority task → evidence crop → measured reduction in costly errors**.

## Our edge
1. **Per-area timeline from the same day.** Several clear frames per area are evidence, not truth: the planogram says what *should* be there, not that the morning shelf was full or compliant.
   - Full reference = the area's highest robust coverage over the day, not "the morning".
   - Occluded frame → nearest clear frame only within a short window, keep its timestamp, never across a restock.
   - Appearance change alone can't tell depletion from rearrangement, lighting or a wrong product; combine with the VLM.
2. **Cost-aware answers** from calibrated probabilities (below). Never skip an area (missing = −5).
3. **Proof.** Local copy of the scoring function, held-out evaluation, every component compared against baselines.
4. **Stretch:** time-to-empty from the fill curve, only if it can be validated; otherwise "future work" in the pitch.

## Decision rule
Stock payoff (rows = prediction, cols = truth):

| | empty | half | full |
|---|---|---|---|
| empty | +1 | −2 | −2 |
| half | −3 | +1 | −2 |
| full | −3 | −3 | +1 |

With calibrated probabilities e, h, f pick the largest of:
- S_empty = 3e − 2
- S_half = −3e + h − 2f
- S_full = 4f − 3

Compliance (+1 / −2, symmetric): predict mismatch when calibrated P(mismatch) > 0.5. The compliant prior is already inside that probability; no extra threshold.

Token probabilities are measurements, not probabilities: sum all variants of each label token (`empty`/`Empty`/` empty` are different tokens), normalise over the allowed labels at the same position, then calibrate. Raw VLM output was 0.999 on a test image.

## Models
| Role | Pick | Fallback / comparison |
|---|---|---|
| VLM judge | Qwen3.8-27B (on knuth, tested: 54.7 GB VRAM, 0.27 s/question) | Compare against Qwen3-VL-32B (on knuth) on identical crops by actual score. Gemma 4 31B only if both fail. |
| Produce coverage / occlusion | SAM 3, text prompts + visual exemplars (gated on HF) | Grounding DINO + SAM 2 |
| Change detection | DINOv3 ViT-L/16, patch features inside the area (gated on HF) | ViT-B/16 if speed is a problem; DINOv2-large |

Run model stages sequentially; measure end-to-end seconds per area.

## Pipeline (`ml/`)
1. **Submission first:** one command writes the exact JSON (every expected image/area key, real booleans, consistent `stock_level`/`stock_value`), with a deterministic fallback if a model fails. Schema check in `scripts/smoke_test.sh`.
2. **Crops:** warp each area quad to a rectangle with a **valid-pixel mask** (negative coordinates = padding, never counted as empty shelf). Tight crop + context image (full frame, area outlined).
3. **Timeline (sampled frames, expand where useful):** DINOv3 patch features, SAM 3 coverage of **generic produce** (not the expected product, or a wrong product looks empty), person/hand flag.
4. **VLM judge:** tight crop + context + reference crop → P(compliant), P(empty/half/full).
5. **Calibration / fusion** over [VLM probs, coverage vs reference, patch distance]. Only if the mentor allows hand-label calibration (it is supervised, the brief stresses no labels).
6. **Decision** with the rule above.
7. **Local scorer** on every change; numbers to `docs/RESULTS.md`.

Coverage is not pile volume (removing a top layer barely changes it); the VLM covers that.

## Evaluation
- Baselines: always compliant + each constant stock level (empty, half, full); plain VLM most-likely answer; then each component added separately.
- Hand labels sampled across cameras, products, stock states and occlusions. Split by **area / time block**, never random adjacent crops. Representative holdout kept separate from hand-picked hard cases.
- Two people label the same 30 to measure disagreement on "half". Small gains below that noise don't count.

## Product (`api/` + `ui/`)
- Staff app opens on a **priority list**: restock now / wrong product / OK, sorted by cost to the store.
- Area detail: current crop next to reference, fill over the day, one-sentence reason. Show an occluded case honestly.
- Output JSON = annotation format exactly. Richer per-area record in `docs/CONTRACT.md`.
- Retrospective analysis (uses later frames) vs live monitoring: say which one the demo shows.
- **MongoDB only with a confirmed prize:** one ordinary `observations` collection keyed by camera, image, area, run; images/embeddings stay outside; polling, not Change Streams (not supported on time-series collections). Local JSON stays the submission source and offline fallback.

## Roles
- Diogo: perception (`ml/`).
- Emanuel: product (`api/`, `ui/`).
- Reviewer agent (own worktree): scorer, labelling tool, schema checks, ablations, reviews against `docs/CONTRACT.md`, pitch challenge.

## Schedule
| When | Goal |
|---|---|
| Fri night | HF access for SAM 3 / DINOv3; knuth env `jx` + Qwen3.8 ready (done) |
| Sat 12–13 | Data look (timestamps, frames per camera, validation from same day?); mentor questions; draft `CONTRACT.md` |
| **15:00** | Baseline JSON passing schema check + working list/detail screen |
| 15–19 | Scorer on hand labels; VLM vs constant baselines; Qwen3.8 vs Qwen3-VL-32B |
| **19:00** | Submission-ready artifact (confirm separately when Sensei validation opens) |
| 19–07 | **One measured improvement at a time** (timeline → calibration); sleep in shifts |
| **Sun 10:00** | ML freeze, final submission |
| 10–13 | Demo polish, cached fallback, rehearse 3 min ×3, `DEMO.md` fallbacks |

Cut order if behind: forecasting → store map → MongoDB → all-frame processing.

## Mentor questions (before building fusion)
- How often can we submit validation outputs, and from when?
- Does an empty area count as compliant? How are partly visible areas annotated?
- Is calibrating on our own hand labels allowed?
- May we use other frames from the same day (including later ones) as context?
- Are validation images from the same day/cameras as train/test?
- Are cloud VLM APIs allowed? How is the general prize judged?

## Risks
- Annotation semantics ("half", empty-area compliance) can erase small gains on our own labels.
- Small crops (~165×90 px): upscaling presents detail, can't create it → add context.
- VLM overconfidence → calibration is required, not optional.
- Validation from another day → timeline edge mostly lost; fall back to cost-aware VLM.
- knuth: `/workspace` only, ~45 GB free; never delete pre-existing files. Wi-Fi: test SSH over phone hotspot.
