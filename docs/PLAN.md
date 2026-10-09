# Plan — Sensei: Fresh eyes on fresh produce

Challenge choice is conditional: if no measurable edge by hour 3, switch to QuantumTrace (Inspiring Solutions).

## Objective
> Every area calibrates itself against its own day, and every answer is the one that costs staff least.

Two prizes, two targets, planned from hour 0:
- **Sensei prize** = automatic score on 289 hidden validation areas (max 578). Owned by `ml/`.
- **General / Peer prize** = demo and pitch. Owned by `api/` + `ui/`. Last year's winner (Forest Guardian) won with a known model (YOLOv8-seg) wrapped in a complete product: upload → instant result with confidence maps, clear impact story, production-looking architecture.

## Our edge
1. **Per-area timeline from the same day, no labels.** Earliest frames = area full and compliant (planogram is valid "at the start of the day"). Stock = how much of its morning self is left. Compliance = did it change from its morning look. Occluded frame → nearest clear frame in time.
2. **Cost-aware answers.** Calibrated probabilities, pick the answer with best expected score. Never skip an area (missing = −5).
3. **Proof.** Local copy of the scoring function, hand labels used only to measure and calibrate, every change compared against two baselines.
4. **Time-to-empty forecast** per area from the fill curve (brief's "future potential"; strong for the general jury).

Stock payoff (rows = prediction, cols = truth):

| | empty | half | full |
|---|---|---|---|
| empty | +1 | −2 | −2 |
| half | −3 | +1 | −2 |
| full | −3 | −3 | +1 |

Identification: +1 right / −2 wrong (symmetric). Flag a mismatch only on strong evidence; the prior is probably "compliant".

## Models
| Role | Pick | Fallback |
|---|---|---|
| VLM judge (one-token answers, read as probabilities) | Qwen3.8-27B (dense, ~55 GB bf16, `enable_thinking: False`) | Qwen3.6-27B → Qwen3-VL-32B (on server) |
| Produce coverage / occlusion (text-prompted masks) | SAM 3 (gated on HF) | Grounding DINO + SAM 2 |
| Timeline / change detection | DINOv3 ViT-L/16 (gated on HF) | DINOv2-large |
| Second opinion (only if Qwen does badly) | Gemma 4 31B | — |

## Pipeline (`ml/`)
1. **Ingest:** parse `planogram.json`, index images by camera and timestamp. Warp each area quad to a rectangle; pad negative coordinates. Context image = full frame with the area outlined.
2. **Timeline (all frames):** per area per frame: DINOv3 embedding, SAM 3 produce coverage, person/hand flag → full reference, coverage curve, nearest clear frame.
3. **VLM judge:** context image + current crop + morning reference → P(compliant), P(empty/half/full).
4. **Fusion + calibration:** logistic regression over [VLM probs, coverage vs morning, embedding distance], cross-validated on hand labels.
5. **Decision:** expected-score answer from the payoff matrix.
6. **Local scorer:** exact scoring, run against both baselines on every change. Numbers go to `docs/RESULTS.md`.

Baselines: (a) always compliant + one fixed stock level; (b) plain VLM, most likely answer.
Hand labels: ~100 areas via the labelling tool; two people label the same 30 to measure disagreement on "half".

## Product (`api/` + `ui/`)
- Staff app opens on a **priority list**: restock now / wrong product / OK, sorted by cost to the store.
- Area detail: current crop next to morning reference, fill curve over the day with time-to-empty, one-sentence reason.
- Store map of the 14 cameras with coloured areas.
- Output JSON = annotation format exactly. Richer per-area record (probabilities, crop URLs, timeline) defined in `docs/CONTRACT.md`.
- **MongoDB Atlas (only if there's a MongoDB prize):** result documents, time-series collection for fill curves, Change Streams for live alerts. Bulk embeddings stay local (M0 = 512 MB). Keep a local JSON fallback (venue Wi-Fi).

## Schedule
| When | ml | api | 3rd member / shared |
|---|---|---|---|
| Fri night | HF access for SAM 3 / DINOv3; new env; Qwen3.8 one-image test, speed | Contract, API stack choice | Ask on Discord about MongoDB prize; Team Finder |
| Sat 12–13 | Data look: timestamps, frames per camera, validation from same day? | Draft `CONTRACT.md` together | Mentor questions |
| 13–15 | Crops + scorer + both baselines | API skeleton + labelling tool | Labelling |
| 15–19 | Timeline, VLM with references, calibration, decision. **Kill checkpoint at hour 3** | API serving mocks; UI list + detail | Labelling, agreement check |
| **19:00** | **First validation submission (baseline)** | | |
| 19–02 | Ablations, time-to-empty, results table | UI on real outputs; MongoDB if prize | Pitch outline |
| 02–07 | Sleep in shifts; long jobs run unattended | | |
| 07–10 | **ML freeze 10:00**, final submission | Demo polish, cached fallback | Slides, architecture slide |
| 10–13 | Rehearse 3 min ×3, `DEMO.md` fallbacks | | |

## Kill criteria
1. 45 min: scorer + baseline on dev labels.
2. Calibration + expected-score decoding: keep only if dev score rises.
3. Per-area timeline: keep only if it helps.
4. No edge by hour 3 → QuantumTrace.

## Mentor questions
- How often can we submit validation outputs?
- Does an empty area count as compliant?
- Are validation images from the same day/cameras as train/test?
- Are cloud VLM APIs allowed?
- How is the general prize judged (pitch weight)?

## Risks
- Crops are small (~165×90 px) → context image + upscaled warp.
- "half" is subjective → measure label disagreement, lean low.
- Validation from another day → timeline edge mostly lost; fall back to cost-aware VLM.
- Server disk: `/workspace` only (~45 GB free after models). Wi-Fi: test SSH over phone hotspot.
