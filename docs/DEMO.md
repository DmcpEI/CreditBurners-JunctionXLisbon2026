# Demo

Status: working local Spring/React app on saved real predictions from `qwen3.8-27b-ctx640-lora-emptycheck-alwayscompliant-full-v1` (fine-tuned model). Store view (simulated live view with urgency per camera and a per-camera filter), alerts, camera/crop evidence and the Shelf study (store / camera / product insights for the recorded day) are implemented. Public deployment/QR and the final presentation rehearsal remain pending. Current continuation instructions: `docs/PLAN.md`, Member2 continuation.

Challenge confirmed: Sensei. The script below demonstrates the shelf assistant and its measured results.

## One-sentence pitch
We turn existing store cameras into a prioritised list of shelf tasks, with visible evidence so staff can decide what to restock or inspect.

## What judges can try
- Open the phone-friendly app without installing anything (local Wi-Fi now; public QR still pending).
- Store view: open a camera or priority shelf task and inspect the crop/full-camera evidence.
- Shelf study: switch Whole store / Camera / Product; read when shelves run low by hour, which products are most often low or rarely low, where stock moves most and the slowest refills; open any row's evidence.
- Watch a short recorded sequence and see tasks change with the actual observations.
- Stretch: request fresh inference on an approved image. Further stretch: photograph one produce tray and select the expected product.

The core demo works from saved results. Label it "Simulated live view (recorded data)" and show the last-seen time, as the app does. "Analysed now" means fresh processing, not a live camera feed. Mark reference timestamps and any use of later frames. Never describe a saved result as fresh inference.

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
- Current integration data: `results/qwen3.8-27b-ctx640-lora-emptycheck-alwayscompliant-full-v1/snapshots.json`. The old `data/prepared-v1/snapshots.json` is a constant baseline available only by explicit override; never present it as model output.

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

## Current app and verification

The default export contains 181 frames / 1,962 observations: 200 empty, 639 half, 1,123 full, including 8 fallbacks. Product identity is not assessed (`product_check: not_assessed`); fixed compliance=true must never become a verified-product badge. Staff UI deliberately omits technical product-check notices. Fallback/unusable shelves remain neutral/unassessed and are excluded from study counts and reliable stock alerts. Source files and model values are never rewritten by UI controls. `?demo=1` is an explicitly labelled illustrative preview preserving supplied values; not evaluation or inference.

Store view is a simulated live view: each camera's latest capture, labelled "Simulated live · recorded data" with a red live dot and last-seen times. Camera cards show urgent/soon counts and are sorted by urgency; tapping a camera filters the shelf list to it ("Show all cameras" resets), while the bell always lists every camera's alerts. Empty/half/full backgrounds and polygons use red/amber/green with neutral card borders. "Restock urgently" means empty; "Restock" means half. Desktop hero preview has camera arrows and clickable regions; hidden on mobile. Back restores the list position.

Shelf study: Whole store / Camera / Product scopes over the recorded day: share of checks low, median wait empty → refilled, lasting stock changes, stock by hour, products most/least often low, zones with most movement, slowest refills (each opens evidence). Whole store on 27 Jun: 43% of checks low; fullest 10:00 (72% full), lowest 19:00 (41% full), first image 06:00 30% empty; median 2 h 15 min to refill (12 refills, 15 not refilled by the last image); most movement cameras 6376 and 6491. The data cannot prove sales or customer movement; hour-scale gaps bound refill times.

Alerts are derived from the latest selected saved data: a new observation with no issue removes the corresponding task, but there is no automatic ingestion or manual completion database. Login, staff roles, assignment, vibration/push notifications and fresh-analysis jobs are not implemented.

Latest integration verification: 15 preparation/scoring smoke tests, 14 frontend tests, Vite/Maven builds and `api/verify.py` passed. On an isolated port, verified the recommended run and explicit product-check metadata, all 181 indexed frames/assets, 14 camera cards/152 latest shelves, no 390px overflow and study ranking → crop navigation. Physical device/public/mobile-data access and full per-camera polygon review remain unverified. Temporary test servers were stopped; user-owned IntelliJ processes were not stopped.

## Run locally

From the repository root, with Node, Java17+ and Maven installed, and `data/prepared-v1/assets` prepared as described in CONTRACT:

```bash
npm ci --prefix ui
npm run build --prefix ui
mvn -f api/pom.xml package
java -jar api/target/sensei-0.1.0.jar --sensei.data-dir=data/prepared-v1 --server.address=0.0.0.0 --server.port=8080
```

Open http://localhost:8080. For a phone on the same Wi-Fi use `http://<Mac-LAN-IP>:8080`; get the IP with `ipconfig getifaddr en0`. The Java process serves the built UI and reads the export only at startup. Stop with Ctrl+C before rebuilding/replacing its running JAR. If 8080 is user-owned, choose 8082 and use that URL for verification.

For React development, leave the API running and in a second terminal:

```bash
npm run dev --prefix ui -- --host 0.0.0.0
```

Use the URL printed by Vite (API/assets proxy to 8080). `npm run build` is required for the Java-only version to include UI edits. Stop each process in its own terminal with Ctrl+C.

```bash
PYTHON=.venv/bin/python bash scripts/smoke_test.sh
node --test ui/tests/*.test.js
python3 api/verify.py http://127.0.0.1:8080
```

IntelliJ is intentionally local-only: `.idea/runConfigurations/Sensei app.xml` starts `team.creditburners.Application` using module `sensei`, repo-root working directory, frontend build before launch, and `--spring.web.resources.static-locations=file:./ui/dist/,classpath:/static/`. Import `api/pom.xml` as Maven and configure Java/Node if setting up another machine. A local `.idea/sensei.iml` was registered to address “module not specified”; no IDE configuration was committed. Run-button execution remains unverified; reopen/import if configuration changes are not picked up.

## Defence: new organiser images

Keep the original supplied dataset and its planogram unchanged. New validation input can be a separate folder or ZIP; do not overwrite the original images. Member1 owns inference/submission. From the root:

```bash
scripts/run_validation.sh data/validation-input defesa-01
```

Expected final submission: `data/val-defesa-01/export/submission.json`; app records: `data/val-defesa-01/export/snapshots.json`. Choose a new run name each time: the script rejects an existing output folder. It uses the original planogram to infer/validate camera mapping and rejects unsuitable inputs; inspect its crops contact sheet. It prepares/infers on knuth and downloads JSON, not the full local image/crop inventory. If knuth fails it explicitly emits a half/compliant fallback; disclose that, never call it real inference. Final validation timings/metrics are in RESULTS; no GPU validation was rerun during this UI integration.

To display the new results in the app, also prepare the validation assets locally (requires Pillow and valid camera mapping), in a separate folder:

```bash
python3 -m ml.validate data/validation-input --output data/val-defesa-01-assets
java -jar api/target/sensei-0.1.0.jar --sensei.data-dir=data/val-defesa-01-assets --sensei.snapshots-file=data/val-defesa-01/export/snapshots.json --server.address=0.0.0.0 --server.port=8080
```

Preparation creates images and rectified crops; it does not run the model. Confirm every JSON image/crop URL resolves to that local assets folder before presenting. This fresh-input-to-app procedure has not been rehearsed in this session; do it with Member1 before the defence. Generic handheld/store images without matching camera/planogram geometry are outside the current pipeline. Copying photos into the original dataset folder alone does not analyse them or refresh the app.

## Pitch evidence and efficiency

Use the latest measured evaluation in RESULTS and name the labelled sample and pipeline. Current report has median 3.81 s / camera image on the measured hardware; cached browser replay is not inference time. Include a tariff assumption for cost estimates and distinguish warm processing/cold loading. Official hidden-validation accuracy is not yet claimed. User-visible images and stock conditions may differ between cameras' capture times; never describe the gallery as a live feed.
