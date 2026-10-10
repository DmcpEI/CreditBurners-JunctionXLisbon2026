# Demo

Status: no deployed app, public URL or rehearsed sequence yet. Local preparation provides real images/crops with constant-baseline records for integration; these are explicitly marked as fallbacks, not model predictions.

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
- Application and hosting are not yet implemented; model smoke tests do not verify the demo path.
- Small/occluded crops and hidden pile depth limit visual stock estimates.
- Closed white refrigeration curtains conceal shelves on early 6383/6386 frames; do not call them empty. Hour-scale frame gaps prevent claims about exactly when shelves changed or how quickly stock sold.
- Phone-photo accuracy, browser latency and concurrent use are untested.
- Knuth project/hosting use is authorised. Public image permission, public URL and domain/tunnel setup remain to be confirmed.


## New efficiency criterion

Pitch must include estimated cost per analysed source image, alongside accuracy/points. Measure all areas in an image, not a single crop, and distinguish warm computation, cold load and cached replay. State hardware, precision, image/area counts, throughput and the tariff assumption. Current provisional extrapolation is ~15.2 seconds per source image, or 0.00422×hourly machine rate per image; it is not a direct full-frame measurement. Do not claim donated knuth access makes computation free or use cached UI response time as inference time. Smaller models and YOLO are candidates, not demonstrated savings. Exact new judging weights remain unspecified.
