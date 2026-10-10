# Plan — Sensei: Fresh eyes on fresh produce

Challenge confirmed: Sensei. Team: two people, Member1 and Member2. Final validation is only available at the end; reserve time for inference and submission. Cut scope if progress is slow.

## Resume here — latest organiser updates

User requests a complete handoff because current agent credits may run out. Read this section, then Current handoff below and the top of `docs/RESULTS.md`. Do not restart annotation or broad model research.

**Stock definition (organiser, refined by the team, 10 Oct evening):** empty = nothing left or only about one purchase (a single package, bag or bunch, or a couple of loose items); staff must replenish urgently. half = more than one purchase left, but staff would take the time to replenish now. full = well stocked; not worth replenishing yet. **In case of doubt, choose the lower level** (Sensei: over-estimate −3 vs under −2; our 3/7 half rule). Used for stock prompt v4, label protocol `sensei-replenish-v5` and all future labelling; existing frozen labels stay unchanged (corrections are a new version).

**New confirmed rules:** (1) processing resource/cost efficiency now contributes to judging; pitch must estimate cost per analysed image. Exact weighting/formula was not provided. (2) An actually empty area is planogram-compliant. Do not equate all nearly-depleted stock predictions with zero objects: wrong visible produce can still be non-compliant even if stock is classified empty. (3) Curtains are outside final validation; exclude confirmed curtain images from accuracy metrics and do not spend more effort tuning them.

**Code change made after last benchmark:** `inspect_stages` now returns compliant=true when presence says no produce; tests updated. The 60 frozen human labels and historical metrics have NOT been silently modified. Some truly empty examples have null compliance under the previous protocol. Make an explicit derived GT revision or ask for confirmation of affected genuinely-empty entries before reporting revised compliance denominators. Do not use model predictions to decide ground-truth emptiness, and do not set all human stock=empty entries compliant automatically: some contain near-empty produce.

**Done since (see top of `docs/RESULTS.md`):** dev error review (all 10 errors half→full/empty, bare floor visible); stock prompt v2 rejected (15/55 vs 16/55); Qwen3.5-4B rejected (0/55, needs `--answer-prefix`, ~3× faster). Fixed rule "half if stock B ≥ 0.15" (`ml/decision_rule.py`) tested once on cached holdout: −5/44 → 10/44 (dev 16/55 → 40/55). Current pipeline: Qwen3.8-27B, prompt v1, then this rule. Label-tuned, not calibrated; holdout was previously inspected. Review set v2: 140 human labels frozen (`data/ground-truth/human-v3-frozen.json`). Full export built (`data/full-v1/export/`, 16 s/camera image) but on 70 fresh evaluation areas it loses to constant full+compliant (11 vs 34/140); compliance false alarms are the main loss. Decided: always compliant. Current best pipeline: **stock question (prompt v1) + half rule 0.20 + empty check (prompt v4, empty if A ≥ 0.70) + always compliant, 640 px camera context**; ~5.8 s per camera image (was 16 s this afternoon); export in `results/qwen3.8-27b-ctx640-half020-emptycheck-full-v1/`. Labels: v2–v4 frozen + r2 corrections (refined definition). 298 labelled observations. Final validation: `scripts/run_validation.sh <images> <name>` (rehearsed: 26 images in 3 min; offline fallback tested). SAM 3 coverage tested, not adopted. Blind review batch v3 (98 crops) on port 8767.

**Next steps (agreed order):**
1. User explains the 10 development errors using `http://127.0.0.1:8765/errors.html`. Page shows frozen truth, model decision, crop/context and editable notes; Export review notes saves a separate JSON. It does not edit labels. Local artifact created; browser interaction on this new error page has not yet been tested. Do not review/tune against holdout errors.
2. Turn those explanations into ONE controlled stock-prompt change. Compare against development baseline (20/30, 16/55) using same inputs, fixed fallback and cached unchanged questions. Main failure: 9 half→full errors. Do not confuse exact-polygon capacity with whole physical-tray capacity or raw fruit count. Test a validation-only no-visibility path separately; guaranteed-visible images should not be rejected as hidden. Keep change attribution clear.
3. Establish efficiency measurement with model preloaded, batch size stated, no cached question timings mixed in. Report complete source-camera image processing (all its areas), total wall time, p50/p95, peak allocated GPU memory, model/precision, cold-load separately, fallback counts and quality/points. CPU work and preprocessing count in end-to-end measurements. Optional sampled power measurements support energy claims; a single nvidia-smi power reading does not.
4. Compare ONE smaller VLM first: `Qwen/Qwen3.5-4B` or `Qwen/Qwen3-VL-4B-Instruct` (official model cards verified this session). Neither is downloaded. `/workspace/models` currently has only qwen3.8-27b, qwen3-vl-32b-instruct, sam3, dinov3-vitl16. User authorised knuth project use including setup; check free disk before downloads and preserve other jobs. No download/install started. Use a fresh model cache identity, same development cases and protocol. Select for measured points versus cost, not parameter count alone.
5. YOLO is a bounded optional comparator, not a replacement assumption. COCO-pretrained models have limited produce classes and no half/full capacity semantics. Our labels are area classes, not individual-fruit bounding boxes; do not pretend they are detector-training annotations. Compare only supported classes or a justified explicit adaptation. Open-vocabulary detection could be a later option; no YOLO code/model is installed or tested here.
6. Once the chosen candidate improves development quality/cost, create complete Sensei JSON and app snapshots, validate all keys, then run the full supplied dataset. Keep the current holdout benchmark as already exposed; further claims need a declared new test protocol. Connect Spring/React demo, deploy and rehearse. No full model export or public app yet.

**Cost estimate to present honestly:** current uncached holdout run has ~1.40 s median per area; dataset average is 1,962/181≈10.84 areas per source image. A rough serial extrapolation is ~15.2 s per camera image; not a measured full-frame benchmark. At an explicitly hypothetical machine rate R currency/hour, allocated compute cost ≈15.2/3600×R = 0.00422R per image (e.g. 0.00422 at R=1). Actual knuth billing rate, electricity and depreciation are unknown. Donated access is not evidence of zero processing cost. Replace this estimate with direct full-image timing and a stated real or hypothetical tariff before pitching. No fabricated provider quote or claimed cost saving.

**Verified references:** https://huggingface.co/Qwen/Qwen3.5-4B ; https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct ; https://docs.ultralytics.com/datasets/detect/coco/ . These verify candidate availability/class scope, not performance on our dataset.

## Current handoff — 10 October 2026

Human local ground truth is collected and frozen: 60 reviewed observations, protocol `sensei-box-capacity-v2`, source `sensei-93b9d1c2db63ec53-frozen.json` at repository root; working copy `data/ground-truth/human-v2-frozen.json`. Preserve both. Generated data and labels remain local/untracked; do not assume a fresh clone includes them. Labels were assistant-prefilled and human-reviewed, so report assisted annotation, not blind annotation.

**Rules confirmed by Sensei via the user:** only the supplied polygon counts; stock is relative to capacity for that product; nearly depleted can be empty even if produce remains. Large-fruit count cannot be compared directly with small-fruit count. Discard closed-curtain observations from stock/product metrics; final validation will be visible. Keep all requested final submission keys even if the model mistakenly abstains. Knuth project use is authorised; work in `/workspace`, preserve unrelated files/processes. Image redistribution is a separate permission.

**Implemented:** data preparation and geometry masks; diagnostic staged Qwen inference; per-question caching; human annotation page; validated local-reference evaluator with fixed baselines. Presence/compliance use crop+mask; visibility/stock also use camera context. Stock now offers empty/half/full/unknown even when produce is present. Ground-truth labels never go into model prompts. Model weights/environment on knuth are unchanged.

**Current data:** 181 images / 14 cameras / 1,962 area observations. Human reference: 32 development and 28 area-disjoint holdout observations. Two curtains in each split are excluded from stock/product scores. Frozen output hashes, metrics and exact rerun commands live in `docs/RESULTS.md` under Latest evaluation and agent handoff.

**Development result:** stock 20/30 (66.7%); combined task score 16/55 versus best constant baseline -1/55. Main error: nine true-half areas predicted full. All 25 definite compliance labels are positive, so 25/25 match is not evidence of real mismatch detection. Holdout with the same fixed prompt: stock 15/26 (57.7%), combined points -5/44 versus half baseline -6/44. It is now exposed; do not tune against its errors and still call it untouched.

**Next work, in order:** review development half→full failures and compare one controlled improvement using cached inputs; produce complete competition/app exports with disclosed fallbacks; run the full dataset; connect API/UI and measure the demo path. The current diagnostic result files are NOT final competition submissions. Avoid more curtain work. No SAM/DINO stage is in the working pipeline. No deployed app/public URL yet.

**Execution:** local `python3`; knuth `/workspace/miniconda/envs/jx/bin/python`, model `/workspace/models/qwen3.8-27b`. Latest remote runs `/workspace/jx/sensei-eval-dev-v1` and `/workspace/jx/sensei-eval-holdout-v1`. The annotation server is local `http://127.0.0.1:8765`, serving `data/human-review-v1`; restart with `python3 -m http.server 8765 --bind 127.0.0.1 --directory data/human-review-v1` if needed. Existing browser reviews use a protocol-specific localStorage key. Do not regenerate the set or overwrite labels.

**Repo workflow:** `main`; smoke check `bash scripts/smoke_test.sh`; pull --rebase before pushing; no agents in parallel without the user's request. Untracked `projects/` and the original frozen JSON are intentional and must not be swept into unrelated commits. No cloud resources or background knuth jobs were modified by this evaluation.


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
4. **VLM judge (implemented diagnostic):** visibility and stock use tight crop + outlined camera context + aligned validity mask; presence and compliance use only crop + mask to avoid surrounding-scene distraction. Ask visibility first without the expected product; blocked/uncertain → stop and inspect. Exclude human-confirmed curtain views from task metrics. Then ask produce presence; empty → skip product identification, uncertain → inspect. Visible produce proceeds to empty/half/full/unknown (relative to product capacity) and product-match questions. Expected product appears only in the match question. Raw answer scores are uncalibrated; unavailable observations remain null in diagnostics. This is not yet the mandatory scoring export. Reference crops remain a separate optional experiment.
5. **Calibration / fusion** over [VLM probs, coverage vs reference, patch distance]. Self-annotation is confirmed. Any fitting uses only development labels; keep held-out labels for evaluation. Calibration is optional and must demonstrate benefit over the plain model.
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
- **Shelf study:** move historical camera/time selection and recorded replay into a separate study page, as specified below. Keep routine store browsing focused on the latest saved image per camera.
- **Stretch: Analyse now:** fresh inference on an approved store image, with a progress state and measured turnaround. Label saved results as saved, and fresh inference as fresh. Fresh processing of a historical image is not a live camera feed.
- **Further stretch: Try a photo:** upload/take a photo of one produce tray and select its expected product. No arbitrary whole-store uploads. Stock estimation is experimental without a suitable full-tray reference; no borrowed Sensei planogram or same-day history. Test a physical fruit-tray demo before offering it to judges.
- Optional "mark checked" is a staff acknowledgement, not proof stock improved. A later actual observation can establish restocking; do not simulate it as a measured result.
- Keep the mobile interface simple: readable text, large evidence images, clear actions, loading/error states. No chatbot, freshness claims, exact hidden-item counts or unvalidated forecasting.
- Exact Sensei export and richer app records are separate formats in `docs/CONTRACT.md`. Pitch and fallback behaviour live in `docs/DEMO.md`.
- **MongoDB only with a confirmed prize:** one ordinary `observations` collection keyed by camera, image, area, run; images/embeddings stay outside; polling, not Change Streams (not supported on time-series collections). Local JSON stays the submission source and offline fallback.

### Two-page app revision — saved stock results integrated

Implementation status: Store view/Shelf study navigation, latest-camera view, historical archive, shared evidence tools and assessment-gated summary logic and mobile study graphs are implemented. Store tasks and study graphs now use Member1’s recommended saved stock run `qwen3.8-27b-stockonly-half020-full-v1` by default; camera coverage uses actual image counts. Its fixed compliance is disclosed as product match not assessed. Fallback areas are excluded from assessed statistics. Public hosting remains pending.

Keep the current React/Spring app, visual identity, photo cards, alerts, fullscreen evidence viewer, planogram polygons and mobile previous/next controls. Adapt the existing store overview and replay rather than building a second app. Add two navigation links at the top: **Store view** and **Shelf study**. The PDF's core remains per-area stock and planogram compliance; historical study supports that purpose rather than becoming sales analytics.

**Page 1 — Store view (staff, beginning of shift)**
- Show exactly one latest saved image per camera, ordered by capture time within that camera, and all its planogram areas. Never retain an old study-frame selection when returning to Store view.
- Provide camera photo cards and the existing all-area product search/alert filters; selecting a camera opens its full image with clickable polygons and every associated crop. A camera filter may narrow the view but does not expose a historical time picker.
- Selecting a crop opens evidence and both stock/compliance indicators. Staff can switch areas without leaving the camera, using polygons, selector or previous/next controls.
- Keep the bell linked to tasks from these latest observations only. Include both issues when a shelf is empty and mismatched; full stock with the wrong product still needs review. Unassessed and illustrative results must not appear to be reliable operational findings.
- Label this **Latest recorded view**, not a live feed. Each camera may have a different capture time; show its actual date/time, not a single unsupported store-wide timestamp. A later actual live source can use the same layout.

**Page 2 — Shelf study (historical evidence, manager review)**
- First choose a camera, then show every published image for it in chronological order with its date/time. The current dataset has 181 images, 14 cameras and 12–14 frames per camera, with approximately 60–78 minutes between frames.
- Opening an image reuses the interactive full-camera map, crop detail and fullscreen viewer. Keep a selected area when changing frames of the same camera if that area exists; otherwise explain its absence. Preserve camera, frame and area in the URL and Back navigation.
- Reuse manual previous/next frame navigation and the existing optional recorded replay. Move the historical time selector here; do not leave it on Store view.
- The image archive now includes stock distribution, a clickable per-frame stock timeline and camera coverage graphs. Default graphs use saved stock results and exclude mock/fallback observations. Manual preview is opt-in (`demo=1`), preserving supplied values and clearly labelling them as illustrative. Product mismatch rates remain unavailable for the stock-only run.

| Study question | Supported presentation | Limit |
|---|---|---|
| Which shelves were observed empty? | Number and share of assessed observations marked empty, with timestamps and photos | Sampled observations, not hours empty or exact stockout duration |
| Where did stock levels change? | Adjacent clear assessed states such as full → half, half → empty, or empty → half/full | Describe observed decreases/increases, not proven purchases or replenishment events; unknown intervals break comparisons |
| Where did planogram mismatches appear? | Mismatch observations / assessed comparable observations, by area and camera | Not measured model accuracy; one mismatch across several frames may be one unresolved issue |
| Which areas need repeated review? | Repeated empty/mismatch observations for the same area, with their history | Do not imply independent incidents or duration between captures |
| How much evidence is usable? | Frames and areas available, missing/unassessed/obstructed observations | Distinguish visibility assessment from ML fallback and missing coverage |

Do not rank cameras by raw alert totals: they have different numbers of areas and frames. Show numerator, denominator and unassessed coverage when comparing rates. Do not aggregate empty/half/full as item counts or treat `stock_value=0.5` as a measured 50% of inventory. Repeated products remain separate areas; optional product grouping must preserve those areas and use exact catalogue identity if available.

**Claims outside the available evidence**
- No most-purchased products, units sold, revenue, waste, customer footfall, busiest-camera ranking or time-to-empty forecasts from the supplied snapshots alone.
- Photos may show visible people or changes, but no person tracking or movement metric exists in the current contract. A future explicitly evaluated visual-change measure would be a proxy, not sales or footfall.
- Charts describe model predictions on sampled images, not ground truth. Do not show accuracy percentages without labels. Exclude mocks/manual preview/fallback records from study statistics; show an unavailable state until enough comparable real predictions exist. Manual preview can demonstrate presentation, never trends or measured conclusions.
- Disclose retrospective model context wherever applicable. Later-image context is not a historical live decision.

**Mobile layout**
- Two clear top navigation items. Keep Store view compact: search, tasks and images close to the first screen; keep larger branding treatment on desktop.
- Camera cards show capture date/time and number of areas. The study camera picker and date/time selection stay accessible without overcrowding the screen.
- Use a vertical frame archive and stacked study summaries. Avoid wide tables or tiny chart targets; every summary links to readable evidence.
- Reuse fixed thumb-reachable previous/next shelf controls, stable scroll, touch targets, focus/Back restoration and reduced-motion behavior. Frame controls must be clearly distinguished from shelf controls.

**Delivery order and scope cut**
1. Adapt navigation and guarantee latest-per-camera Store view; move historical controls to Shelf study. Preserve the existing demo path and no-inference browsing.
2. Ship the historical image archive using the existing endpoints/cache and shared evidence components. Verify original capture times, same-area frame switching, Back/deep links, errors and mobile widths.
3. Integrate Member1's complete real snapshots, remove the temporary default manual preview, and check baseline/mock/unknown exclusions.
4. Add empty/mismatch observation summaries and observed stock transitions only after step 3; test their denominators and unknown-gap behavior. Keep the official scoring/export in Member1's area.
5. Rehearse latest view → task → camera evidence → historical comparison. Public HTTPS/QR, image-publication permission and laptop fallback remain required work.

The full study/analytics implementation exceeds a 30-minute task. If time is tight, ship steps 1–3 and the archive; cut charts, product ranking and any new inference pipeline. Login, assignment, push notifications and completion tracking remain separate future work. No new API shape or ML output is assumed; coordinate contract changes before introducing additional fields.

## Stack and hosting
- **ML:** Python + PyTorch on knuth; Qwen3.8 with SAM 3 / DINOv3 retained only when they improve measured results.
- **API:** Java / Spring Boot. **UI:** React + Tailwind; serve the built UI and API from one origin.
- **Core integration:** Python writes JSON results and image files; Spring serves them to React. No database or separate Python web server required for browsing/replay.
- **Public deployment:** app on knuth, exposed through Cloudflare Tunnel to an HTTPS URL and QR code, with server use authorised; outbound connectivity and public access still need testing. Expose only the web app; keep inference and filesystem access private. Hosting is planned, not deployed.
- For fresh analysis, Spring accepts bounded jobs and hands them to one persistent local Python worker. Poll job status; limit concurrency and queue length. No Redis/Celery or additional GPU rental for this scope.
- Only publish an approved subset of challenge images; confirm image-sharing permission with Sensei. Use team-owned produce photos if public redistribution is not allowed. Keep validation images and labels out of the public gallery.
- If uploads are built, validate decoded image type, byte size and dimensions, use generated file names, and delete temporary uploads after processing. Restrict gallery requests to known IDs; never accept arbitrary server paths or remote fetch URLs.
- Serve saved results without GPU work. A worker failure leaves browsing available and marks fresh analysis unavailable; do not silently substitute saved output for a fresh request.
- Keep the built app, permitted images and results on a laptop for a local demo if knuth or the public link fails. Test the public URL from mobile data and the local fallback before judging. See `docs/DEMO.md`.

## Roles
- **Member1:** crops, model inference, exact submission export, scorer, labelling, evaluation, error analysis and final validation run. Start with one actual camera image and plain Qwen3.8; deliver every area's prediction in the agreed JSON formats.
- **Member2:** Spring API, React Store view/Shelf study with shared list/detail/replay, public hosting, QR code, mobile presentation and laptop fallback. Start with a synthetic contract fixture; replace it with Member1's real outputs as soon as available. No database required for the core.
- **Together:** inspect the first image/planogram and confirm the contract, answer mentor questions, integrate the first real result, select demo evidence and rehearse. Member1 explains methods/results; Member2 leads the product demonstration.
- Agents assist only with explicitly assigned bounded tasks, in their own worktrees; no third human or continuously available agent is assumed in the schedule.

## Two-person scope
- Must ship: valid Sensei output, a measured baseline, latest-per-camera Store view with integrated list/detail, a Shelf study image archive with a short recorded replay, public QR access and a local fallback.
- One improvement only after the baseline and integration work; choose it from observed errors, not model novelty.
- Fresh inference on an approved image is the first optional product extension. Phone uploads, physical tray demo, MongoDB, a floor-plan store map and forecasting are deferred. The existing camera-image polygon overlay stays in scope; study charts work now with labelled baseline fixtures; measured stock trends depend on integrated real results.
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
- Self-annotation of stock levels is confirmed; retain the fixed development/holdout split.
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
