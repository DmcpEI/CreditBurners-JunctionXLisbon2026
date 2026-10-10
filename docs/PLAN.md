# Plan — Sensei: Fresh eyes on fresh produce

Challenge confirmed: Sensei. Team: two people, Member1 and Member2. Final validation is only available at the end; reserve time for inference and submission. Cut scope if progress is slow.

Dataset received: 181 images at 1280×720, 14 cameras, 152 areas and 1,962 area observations; no ground-truth labels supplied. Same-camera frames are 60–78 minutes apart. Preparation, validity masks, complete constant baselines and scorer now run locally; results and limitations are in `docs/RESULTS.md`. Next: current-image Qwen inference on a representative sample. Member2 can use the explicitly disclosed baseline app records for integration now.

## Objective
> A store assistant that uses existing cameras to tell staff which produce shelves need attention, why, and what to do next.

Finish line: a phone-friendly app judges can open through a public HTTPS link and QR code, a valid Sensei submission, measured results, and a rehearsed three-minute demo. The core experience uses recorded store images; fresh inference and phone-photo uploads are separate extensions, not prerequisites for a usable public app.

Two prizes, two targets, planned from hour 0:
- **Sensei prize** = automatic score on 289 hidden validation areas (max 578). Owned by `ml/`.
- **General / Peer prize** = demo and pitch. Owned by `api/` + `ui/`. Last year's winner (Forest Guardian) wrapped a known model (YOLOv8-seg) in an immediately understandable result: image → visible detection → useful action. Copy that clarity, not their stack. Ours: **shelf image → priority task → evidence crop → measured reduction in costly errors**.

## Our edge
1. **Per-area timeline from the same day.** Several clear frames per area are evidence, not truth: the planogram says what *should* be there, not that the morning shelf was full or compliant.
   - Reference = a clear, representative observation, optionally selected using robust high coverage. Highest observed coverage is not proof the shelf was full. Later-frame references are retrospective and require permission.
   - The supplied frames are 60–78 minutes apart: do not replace an occluded/curtained frame with its neighbour. References are context only; keep timestamps and do not infer unchanged stock across a gap.
   - Appearance change alone can't tell depletion from rearrangement, lighting or a wrong product; combine with the VLM.
2. **Cost-aware answers** from calibrated probabilities (below). Never skip an area (missing = −5).
3. **Proof.** Local copy of the scoring function, held-out evaluation, every component compared against baselines.
4. **Future work:** time-to-empty forecasting; outside the two-person core scope.

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

Token probabilities are uncalibrated scores: use verified single-token answer codes or sum only verified single-token label variants, then normalise over the allowed classes at the same position. Never take just the first token of a multi-token label (`Banana` is two tokens in both downloaded Qwen tokenizers). Keep full precision internally. A 0.999 output on one image does not establish overconfidence; measure calibration on permitted held-out labels. If calibration is disallowed or unsupported by the data, retain the evaluated baseline and do not advertise calibrated confidence.

## Models
| Role | Pick | Fallback / comparison |
|---|---|---|
| VLM judge | Qwen3.8-27B (on knuth, tested: 54.7 GB VRAM, 0.27 s/question) | Compare against Qwen3-VL-32B (on knuth) on identical crops by actual score. Gemma 4 31B only if both fail. |
| Produce coverage / occlusion | SAM 3, text prompts + visual exemplars (gated on HF) | Grounding DINO + SAM 2 |
| Change detection | DINOv3 ViT-L/16, patch features inside the area (gated on HF) | ViT-B/16 if speed is a problem; DINOv2-large |

Models are downloaded on knuth. These timings are setup smoke results, not challenge accuracy or public-app latency. Run model stages sequentially initially; measure end-to-end seconds per area and per browser request. Keep the selected VLM loaded for fresh requests; queue requests rather than loading models for each visitor.

## Pipeline (`ml/`)
Build order: plain Qwen on one real image → complete JSON export → API/UI integration → local scorer and baseline evaluation → at most one additional perception component at a time. The timeline, SAM 3 and DINOv3 below are candidates, not dependencies of the first working version.

1. **Submission first:** one command writes the exact JSON (every expected image/area key, real booleans, consistent `stock_level`/`stock_value`), with a deterministic fallback if a model fails. Schema check in `scripts/smoke_test.sh`.
2. **Crops:** warp each area quad to a rectangle with a **valid-pixel mask** (negative coordinates = padding, never counted as empty shelf). Tight crop + context image (full frame, area outlined).
3. **Timeline (sampled frames, expand where useful):** DINOv3 patch features, SAM 3 produce coverage, person/hand flag.
   - Candidate SAM 3 prompt strategy = union of masks for the English names of **all products on that camera** (not only the expected one, or a wrong product looks empty) + "produce" at threshold 0.3. Reported Fri on a banana image: "banana" covers 0.76, "produce" 0.97 at 0.3 but 0.20 at 0.5, "fruit"/"food"/"vegetable" ≈ 0. Translate the Portuguese names once. Inspect masks for background inclusion and reproduce the threshold comparison on store crops before adopting it.
4. **VLM judge:** tight crop + context + reference crop → P(compliant), P(empty/half/full).
5. **Calibration / fusion** over [VLM probs, coverage vs reference, patch distance]. Only if the mentor allows hand-label calibration (it is supervised, the brief stresses no labels).
6. **Decision** with the rule above.
7. **Local scorer** on every change; numbers to `docs/RESULTS.md`.

Coverage is not pile volume (removing a top layer barely changes it). The VLM may provide extra evidence, but hidden inventory cannot be reliably recovered from these images.

## Evaluation
- Final official validation is only at the end. Choose methods using the permitted local evaluation; do not plan around repeated official feedback. Confirm release time, processing window, submission deadline and retry rules now.
- Baselines: always compliant + each constant stock level (empty, half, full); plain VLM most-likely answer; then each component added separately.
- Hand labels sampled across cameras, products, stock states and occlusions. Split by **area / time block**, never random adjacent crops. Representative holdout kept separate from hand-picked hard cases.
- Member1 owns labelling and evaluation. Both members independently label the same small subset in one time-boxed session (up to 30 areas if practical), then Member2 returns to the product. Record disagreement on "half"; do not treat small noisy gains as reliable.
- Measure full-batch inference time before final validation and reserve that time plus recovery margin inside Sensei's confirmed window. Freeze model/prompt choices before that run; run schema and coverage checks before submission.
- Record each experiment in `docs/RESULTS.md`: method, reason, dataset/split, result, failure and keep/drop decision. Distinguish local measurements from official results; the presentation should explain the journey as well as the final score.

## Product (`api/` + `ui/`)
- **Needs attention:** product, shelf location, observation time, image and suggested action. Start with a declared severity order (empty, mismatch, half); it is not an estimate of euros lost. Obstructed observations visibly require inspection rather than claiming certainty.
- **Show me why:** large current crop, reference with its own timestamp, short explanation, and visibility limitations. Colour is never the only status indicator.
- **Watch the day:** camera/time selection and a short replay of actual observations. Label it "Recorded store replay"; show the capture time separately from processing time. Select a real depletion, mismatch or restock sequence after inspecting the data.
- **Stretch: Analyse now:** fresh inference on an approved store image, with a progress state and measured turnaround. Label saved results as saved, and fresh inference as fresh. Fresh processing of a historical image is not a live camera feed.
- **Further stretch: Try a photo:** upload/take a photo of one produce tray and select its expected product. No arbitrary whole-store uploads. Stock estimation is experimental without a suitable full-tray reference; no borrowed Sensei planogram or same-day history. Test a physical fruit-tray demo before offering it to judges.
- Optional "mark checked" is a staff acknowledgement, not proof stock improved. A later actual observation can establish restocking; do not simulate it as a measured result.
- Keep the mobile interface simple: readable text, large evidence images, clear actions, loading/error states. No chatbot, freshness claims, exact hidden-item counts or unvalidated forecasting.
- Exact Sensei export and richer app records are separate formats in `docs/CONTRACT.md`. Pitch and fallback behaviour live in `docs/DEMO.md`.
- **MongoDB only with a confirmed prize:** one ordinary `observations` collection keyed by camera, image, area, run; images/embeddings stay outside; polling, not Change Streams (not supported on time-series collections). Local JSON stays the submission source and offline fallback.

## Stack and hosting
- **ML:** Python + PyTorch on knuth; Qwen3.8 with SAM 3 / DINOv3 retained only when they improve measured results.
- **API:** Java / Spring Boot. **UI:** React + Tailwind; serve the built UI and API from one origin.
- **Core integration:** Python writes JSON results and image files; Spring serves them to React. No database or separate Python web server required for browsing/replay.
- **Public deployment:** app on knuth, exposed through Cloudflare Tunnel to an HTTPS URL and QR code, subject to server publication permission and outbound connectivity. Expose only the web app; keep inference and filesystem access private. Hosting is planned, not deployed.
- For fresh analysis, Spring accepts bounded jobs and hands them to one persistent local Python worker. Poll job status; limit concurrency and queue length. No Redis/Celery or additional GPU rental for this scope.
- Only publish an approved subset of challenge images; confirm image-sharing permission with Sensei. Use team-owned produce photos if public redistribution is not allowed. Keep validation images and labels out of the public gallery.
- If uploads are built, validate decoded image type, byte size and dimensions, use generated file names, and delete temporary uploads after processing. Restrict gallery requests to known IDs; never accept arbitrary server paths or remote fetch URLs.
- Serve saved results without GPU work. A worker failure leaves browsing available and marks fresh analysis unavailable; do not silently substitute saved output for a fresh request.
- Keep the built app, permitted images and results on a laptop for a local demo if knuth or the public link fails. Test the public URL from mobile data and the local fallback before judging. See `docs/DEMO.md`.

## Roles
- **Member1:** crops, model inference, exact submission export, scorer, labelling, evaluation, error analysis and final validation run. Start with one actual camera image and plain Qwen3.8; deliver every area's prediction in the agreed JSON formats.
- **Member2:** Spring API, React list/detail/replay, public hosting, QR code, mobile presentation and laptop fallback. Start with a synthetic contract fixture; replace it with Member1's real outputs as soon as available. No database required for the core.
- **Together:** inspect the first image/planogram and confirm the contract, answer mentor questions, integrate the first real result, select demo evidence and rehearse. Member1 explains methods/results; Member2 leads the product demonstration.
- Agents assist only with explicitly assigned bounded tasks, in their own worktrees; no third human or continuously available agent is assumed in the schedule.

## Two-person scope
- Must ship: valid Sensei output, a measured baseline, one integrated list/detail flow, a short recorded replay, public QR access and a local fallback.
- One improvement only after the baseline and integration work; choose it from observed errors, not model novelty.
- Fresh inference on an approved image is the first optional product extension. Phone uploads, physical tray demo, MongoDB, store map and forecasting are deferred.
- Laptop inference remains an optional efficiency experiment after the core is stable. Compare the same held-out examples, score, memory and latency; claim only the hardware actually tested. It must not delay submission or the public demo.

## Schedule
| When | Member1 | Member2 / shared checkpoint |
|---|---|---|
| First 30 min | Together: inspect one real image and planogram; confirm contract and validation window | Together: confirm public image permission, choose demo candidate and check hosting prerequisites |
| By Sat 15:00 | Plain Qwen → complete real JSON + schema check | List/detail on a mock, then integrate the real JSON; do not wait for the full ML pipeline |
| 15–19 | Scorer, permitted labels, constant baselines vs plain Qwen; inspect errors | Host list/detail, add short replay, test HTTPS from mobile data and prepare QR code |
| Sat 19:00 checkpoint | Submission command ready on available images; official validation still pending | Usable public app on saved real results |
| Evening / overnight | Test one improvement against the baseline; record keep/drop decision | Polish the real demo sequence and prepare laptop fallback; fresh inference only if core is stable |
| Overnight | Agree sleep shifts and cache completed work; no requirement to keep building all night | Same; leave shared inputs/results ready before sleeping |
| Sun 07–10 | Freeze candidate; measure batch runtime, verify export and prepare validation run | Verify public URL, QR and local fallback; rehearse together |
| Sun 10:00 onward | No new modelling work; execute final validation when Sensei releases it, check and submit within its confirmed window | No new features; small presentation fixes and rehearsal; cover demo while Member1 handles validation |

The 19:00 milestone is submission readiness, not an official validation result. Sensei's release time and deadline override the nominal Sunday timetable; reserve measured inference time plus recovery margin, even if rehearsal must move earlier.

If behind, drop optional laptop benchmarking and fresh inference first, then unproven timeline/segmentation additions. Preserve the Sensei export, baseline evaluation, public saved-result experience and local demo fallback.

## Definition of done
- Exact submission JSON covers every expected image/area and passes the real smoke/schema checks.
- Judges can open a QR link on a phone and inspect a recorded observation, its task and evidence.
- Replay, saved predictions, fresh inference and any illustrative mock are labelled truthfully.
- Held-out results compare the chosen pipeline with baselines; benefits such as saved money or reduced waste are not claimed as measured without evidence.
- The three-minute story has been rehearsed, including the local fallback. Extra photo features are not required to finish.

## Mentor questions (before building fusion)
- Using the presentation's actual shelf example, show which areas you would label empty/half/full. Does fill refer to visible surface coverage, item quantity or pile height? Are the thresholds the same for all products?
- For an area containing expected and unexpected produce, does one wrong item make it non-compliant, or is there a dominant-product rule? Do planogram polygons split neighbouring products within one visible crate?
- Are the supplied images raw original-resolution frames or annotated/overlaid versions? Are cameras fixed, what is the sampling interval, and do polygons align with the delivered image dimensions?
- Final validation is only at the end: exactly when are images released, how long can inference run, when is submission due, and are retries allowed?
- Does an empty area count as compliant? How are partly visible areas annotated?
- Is calibrating on our own hand labels allowed?
- May we use other frames from the same day (including later ones) as context?
- Are validation images from the same day/cameras as train/test?
- Are cloud VLM APIs allowed? How is the general prize judged?
- May we publish store images/crops on an unrestricted demo URL? Which subset, if any? What are the General/Peer pitch duration and interaction format?

Presentation photos show angled multi-level crates, visible shelf labels, differently stocked areas and strong background colours. These are photos of projected slides, not inference inputs or evidence of the source resolution. Inspect actual crops before choosing preprocessing or thresholds. Shelf labels describe the expected product, not proof of what is physically present; avoid treating label text or crate colour as a substitute for inspecting produce.

## Risks
- Annotation semantics ("half", empty-area compliance) can erase small gains on our own labels.
- Small crops (~165×90 px): upscaling presents detail, can't create it → add context.
- VLM confidence may be unreliable; calibration depends on permitted labels and evidence. Do not present raw scores as trustworthy confidence percentages.
- Validation from another day → timeline edge mostly lost; fall back to cost-aware VLM.
- knuth: `/workspace` only, ~37 GB free at last inspection; never delete pre-existing files. Public hosting/network access still needs testing. Wi-Fi: test SSH over phone hotspot.
- Phone photos differ from ceiling-camera crops; upload accuracy is unproven. Queue fresh requests and measure latency before promising a response time.
