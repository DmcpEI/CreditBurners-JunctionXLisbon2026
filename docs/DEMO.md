# Demo

Status: local Spring/React list, evidence detail and recorded replay implemented; no public deployment, URL or rehearsed sequence yet. Local preparation provides real images/crops with constant-baseline records for integration; these are explicitly marked as fallbacks, not model predictions.

Challenge confirmed: Sensei. The script below demonstrates the shelf assistant and its measured results.

## One-sentence pitch
We turn existing store cameras into a prioritised list of shelf tasks, with visible evidence so staff can decide what to restock or inspect.

## What judges can try
- Scan a QR code and open the phone-friendly app without installing anything.
- Select a camera/time, inspect a priority task, and compare the current crop with its reference.
- Watch a short recorded sequence and see tasks change with the actual observations.
- Stretch: request fresh inference on an approved image. Further stretch: photograph one produce tray and select the expected product.

The core demo works from saved results. Label it "Recorded store replay" and show the capture timestamp. "Analysed now" means fresh processing, not a live camera feed. Mark reference timestamps and any use of later frames. Never describe a saved result as fresh inference.

## 3-minute script
- **0:00–0:20 — Problem:** staff discover shelf problems by walking the store; explain the cost of missing an empty shelf or raising an unnecessary alert.
- **0:20–1:20 — Product:** show a real recorded shelf change, the resulting task, and the evidence detail. Let the judge scan the QR code. If the sequence contains an actual restock, show the later observation resolving the stock issue.
- **1:20–2:00 — Journey and proof:** explain one assumption the real images challenged, one method kept/dropped and why, then show the measured score against the baseline. Name the sample size and distinguish local labels from official validation results. If the official result is not available yet, say so; do not make the pitch depend on it.
- **2:00–2:30 — Journey:** explain that early images included closed refrigeration curtains, so we excluded those from stock evaluation instead of treating hidden stock as empty. Organisers confirmed final validation contains visible products. Show the human annotation process and one measured visible-shelf improvement; curtain handling is a robustness example, not a scored challenge advantage.
- **2:30–3:00 — Opportunity:** explain how existing cameras could support more stores. Reduced waste, recovered sales and saved staff time are potential benefits, not measured claims unless evaluated.

Confirm the actual General/Peer pitch format with organisers. Rehearse three times; adjust the timings to their limit.

Two-person presentation: Member2 leads the problem and product demonstration; Member1 explains methods, failures and measured results. Rehearse before final validation arrives so Member1 can run and submit it during Sensei's confirmed window. Phone uploads and the physical tray are deferred; no third presenter or operator is assumed.

## Evidence and assets to prepare
- Choose one short, understandable sequence from the supplied data after inspection; do not fabricate a restock or change.
- Confirm which images/crops may be shown publicly. Keep validation images and labels out of the gallery; use team-owned photos if needed.
- Record model/run identity and capture times for all displayed predictions.
- Build a QR code for the verified HTTPS URL, with the URL also printed as text.
- Copy the built app, permitted images and saved results to a laptop. Record a short backup walkthrough, explicitly labelled as recorded.
- If trying a physical fruit tray, test phone photos and lighting beforehand. No reliable stock claim without a suitable reference.

## Fallbacks
- **GPU worker unavailable:** public browsing/replay still uses saved predictions; disable fresh analysis with an explicit message.
- **Public link, knuth or venue internet unavailable:** demonstrate the local app on the laptop. Explain that the QR experience is unavailable; do not pretend local access works on judges' phones.
- **Local app fails:** show the recorded walkthrough and say it is a recording.
- **Photo mode unreliable or unfinished:** omit it. The store replay remains the main product.
- No invented model results or impact metrics. Any development fixture must say "Illustrative mock" and must not enter evaluation results.
- Current integration data: `data/prepared-v1/snapshots.json` contains a constant compliant/half baseline, unknown visibility and `fallback_used: true` on every area. Display its explanation. Do not present these records as image analysis or use their alerts as proof of product accuracy.

## Acceptance checks before judging
- Public URL and QR code work from a phone on mobile data; list, detail and replay work on a narrow screen.
- Confirm image-sharing permission and that only the intended assets are publicly served.
- If fresh inference exists: try a few simultaneous requests, queue overflow, worker failure and a repeated request. Show progress/errors and measure complete turnaround.
- If uploads exist: reject empty, malformed and oversized images; keep each visitor's results separate and remove temporary uploads after processing.
- Verify saved browsing without the worker and the laptop fallback without internet. Only stop processes started for this test, with team coordination.

## Known failures
- Public hosting is not implemented. Local API integration checks are in `api/verify.py`; ML smoke checks remain separate.
- Small/occluded crops and hidden pile depth limit visual stock estimates.
- Closed white refrigeration curtains conceal shelves on early 6383/6386 frames; do not call them empty. Hour-scale frame gaps prevent claims about exactly when shelves changed or how quickly stock sold.
- Phone-photo accuracy, browser latency and concurrent use are untested.
- Knuth project/hosting use is authorised. Public image permission, public URL and domain/tunnel setup remain to be confirmed.

## Local verification — Member2

Built React and packaged Spring with 181 prepared snapshots. `python3 api/verify.py` passes snapshot/detail, capture-time consistency, images, bundled frontend, repeated requests, unknown IDs and traversal rejection. WebKit browser checks passed area selection, camera switching, frame navigation and automatic replay; evidence loaded and a 390px viewport had no horizontal overflow. Constant-baseline fallback labels were visible. The four ML smoke tests also pass with `PYTHON=.venv/bin/python`. Public mobile-data access, approved publication subset, real model predictions and the disconnected-laptop rehearsal remain unverified.

## Staff-first frontend verification

The landing gallery uses the latest saved snapshot per camera (14 cameras, 152 areas). Camera/time selection and recorded replay are secondary. On a phone, selecting a shelf opens evidence directly; Back restores the checklist URL, focus and scroll. Product titles hide retail metadata for readability; original labels remain in observation details. Baseline/mock/fallback and retrospective labels remain explicit.

Earlier checklist builds passed WebKit checks for store totals, first-screen shelf visibility at 375px, mobile evidence, Back URL/focus/scroll, search/no-match recovery, camera filtering, all-camera return, replay advance/pause, pause on keyboard focus and reduced-motion behavior. Separate checks passed desktop split view, landscape width, reloaded deep links, missing images, API failure/retry and empty gallery recovery. API integration checks still pass. Browser network failures were test-only simulations, not model evaluation. Public access and the physical-phone/offline rehearsal remain unverified.

Frontend motion: shelf cards reveal on entering the viewport; hover/press feedback and image fades support browsing. Detail navigation uses native view transitions when supported and ordinary navigation otherwise. Reduced-motion preference disables animated transitions. Verified WebKit mobile detail/back, no horizontal overflow, reduced motion, frontend build and live API/assets. No inference is triggered by these effects.

Evidence inspection: open a shelf and select Enlarge image. Switch between Shelf crop and Full camera, zoom up to 300%, scroll to inspect and use Fit to reset. Escape or Close returns focus to the opener. Verified desktop/mobile zoom scrolling, image switching, reset, Escape, focus restoration and body-scroll restoration. Enlargement adds no detail and browsing does not run inference.

Interactive camera view: shelf details include the full recorded camera image with clickable planogram polygons. Select another area by touch, pointer, keyboard, Previous/Next or dropdown without leaving the camera. Geometry is bundled from the supplied planogram at frontend build time; rebuild if that planogram changes. Verified nine regions on camera 6462, polygon selection, next navigation, Enter activation and mobile width. General alignment across every camera and timeline selection persistence still need a broader visual review.

Manual UI preview is now opt-in with `?demo=1`; the default shows Member1’s recommended saved stock results. Preview preserves supplied stock/compliance values without inventing empty/full states or mismatches and clearly labels them as illustrative. Exit preview uses `demo=0`. No files or model outputs are modified; preview is excluded from measured results and submission.

## Store view and Shelf study

The top navigation now separates staff operations from history. Store view always uses the latest saved image per camera, displays camera overview cards and all crops, and has no historical time selector. Mobile initially shows two camera cards with Show all cameras and a shortcut to all shelves. The interactive map, alert panel, fullscreen viewer and fixed shelf controls are retained.

Shelf study offers every saved image for the selected camera, chronological thumbnails, historical selection and optional replay. Selecting another image retains the same area when available; missing areas produce an explanatory notice. Returning to Store view resets to latest captures. Shelf study defaults to saved-stock graphs with fallback/mock observations excluded. Enable demo graphs is an optional, explicitly labelled preview. Historical crops show saved assessments or unavailable-assessment labels as applicable.

Study summaries count clear assessed area observations, empty observations and product mismatches with explicit denominators. Adjacent assessed frames can show observed stock increases/decreases; an unknown/fallback/mock observation breaks the transition. They are not purchases, confirmed restocks, event counts, durations or measured model accuracy. Stock distribution and per-frame stacked bars now use the saved predictions. Optional graph preview preserves supplied values, with no invented changes. Tap a timeline bar to select its evidence image. Camera coverage uses the actual 181 image summaries across 14 cameras; tapping a camera opens its history. Counts are image inventory, not customer movement. No new model calls or source-data edits are needed.

Validation: seven frontend semantic tests (including explicit baseline inclusion, default exclusion and no fabricated transitions), frontend/Maven builds and live API checks passed. WebKit verified latest14-camera/152-area coverage, no Store view time picker, camera6462's13-image archive, same-area historical navigation, return to latest captures, deep-link reload, camera expansion and mobile widths. Reduced-motion screenshots were visually inspected. Study aggregation was initially tested on synthetic fixtures; the integration checks below now cover real saved results. Physical phone/public URL and full camera-by-camera geometry checks remain outstanding.

Graph validation: frontend and Maven builds, live API verification and four ML smoke tests passed. WebKit checked all three graphs, 14 camera bars, clickable frame/camera navigation, demo/original switching and a 390px layout without page overflow. Reduced-motion mobile/desktop screenshots were inspected. Physical-phone chart interaction is not yet verified.

## New efficiency criterion

Pitch must include estimated cost per analysed source image, alongside accuracy/points. Measure all areas in an image, not a single crop, and distinguish warm computation, cold load and cached replay. State hardware, precision, image/area counts, throughput and the tariff assumption. Current provisional extrapolation is ~15.2 seconds per source image, or 0.00422×hourly machine rate per image; it is not a direct full-frame measurement. Do not claim donated knuth access makes computation free or use cached UI response time as inference time. Smaller models and YOLO are candidates, not demonstrated savings. Exact new judging weights remain unspecified.


## Member1 merge and saved-results integration

Merged `origin/main` at `620f40b` into `feat/interactive-shelf-explorer`, preserving both members’ demo notes. Spring defaults to `results/qwen3.8-27b-stockonly-half020-full-v1/snapshots.json`; assets remain under `data/prepared-v1/assets`. Override results with `--sensei.snapshots-file=<path>`. No inference was rerun and no ML result files were edited.

The complete export contains 181 images and 1,962 areas: 130 empty, 656 half and 1,176 full values, including 15 fallback areas. UI labels those fallback areas unassessed and excludes them from graph assessment counts. Product compliance is fixed true by this run, so product badges/details say not assessed and mismatch statistics are unavailable. Stock predictions are model estimates, not ground truth or proof of purchases.

Validation: nine frontend tests, thirteen ML smoke tests, frontend/Maven builds and live API verification passed. WebKit checked all 181 served run IDs and stock counts, latest 152-shelf coverage, saved-data default, absence of false product-match badges, timeline navigation, and a 390px layout without page overflow. Real-data mobile screenshots were inspected. Physical-phone testing, public access and fresh inference remain unverified. Changes are local commits; no push or merge into main was performed.
