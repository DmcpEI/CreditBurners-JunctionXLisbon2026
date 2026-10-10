# Credit Burners

JunctionX Lisbon 2026

Challenge confirmed: Sensei. Two-person team: Member1 (ML/evaluation) and Member2 (API/UI/deployment).

## The idea

A store assistant that uses existing cameras to identify produce shelves needing attention. Staff get a prioritised list of actions, with images explaining each alert.

Our goal is a phone-friendly app judges can open through a public link and QR code: explore a recorded store day, inspect shelf alerts and their evidence, and see measured results. Fresh analysis and single-tray photo uploads are stretch features.

## Planned stack

- Python / PyTorch on knuth: Qwen3.8-27B, with SAM 3 and DINOv3 evaluated as supporting signals.
- Java / Spring Boot API; React + Tailwind interface.
- JSON results and image files; Cloudflare Tunnel for public HTTPS access, subject to permission and connectivity.
- Saved results for immediate browsing and a laptop demo fallback.

## Current status

ML dataset preparation, constant baselines and the Sensei scorer are implemented. Model weights and setup smoke scripts are on knuth; real dataset inference, API/UI and public deployment are not implemented yet. No public demo URL exists yet.

- [Plan, roles and milestones](docs/PLAN.md)
- [Data and API contract](docs/CONTRACT.md)
- [Demo script and fallbacks](docs/DEMO.md)
- [Measured results](docs/RESULTS.md)

## How to run

From the repository root, with Python 3.10+ and Pillow installed (`python3 -m pip install -r ml/requirements.txt` if needed):

```bash
python3 -m ml.prepare new_dataset_hackathon_junctionx_10_oct_2026_v2 --output data/prepared-v1
bash scripts/smoke_test.sh
```

Choose a new output directory for each preparation run; existing outputs are not overwritten. The original ZIP is read directly, ignoring macOS metadata, without extracting arbitrary archive paths.

The supplied dataset ZIP, planogram and challenge PDF are tracked at the team's request. Extracted duplicates, generated crops/results and model weights stay outside Git.

Outputs in the ignored `data/prepared-v1/` directory:
- `assets/`: original images, rectified shelf crops and validity masks (black = outside the image, not empty shelf).
- `index.json`: each crop's identity, dimensions and visible fraction; `expected.json`: required camera/image/area keys.
- `baseline-empty.json`, `baseline-half.json`, `baseline-full.json`: complete constant submissions, always compliant. These are not model predictions.
- `snapshots.json`: contract-shaped records for Member2's integration, using the half baseline with `fallback_used: true`, unknown visibility and an explicit constant-baseline explanation. Assets are local files; `/assets/...` URLs need Member2's server to resolve.
- `report.json`: dataset counts and off-image areas.

When permitted labels exist, score only their annotated areas (extra predictions are ignored):

```bash
python3 -m ml.scoring data/labels.json data/prepared-v1/baseline-half.json
```

`scripts/smoke_test.sh` tests synthetic preparation, geometry, coverage and scoring. It does not yet exercise model inference or the API/UI. No accuracy metric exists without ground truth.

## Member2 local app

Prepare the dataset above first. From the repository root:

```bash
npm ci --prefix ui
npm run build --prefix ui
mvn -f api/pom.xml package
java -jar api/target/sensei-0.1.0.jar --sensei.data-dir=data/prepared-v1 --server.address=127.0.0.1
```

Open http://127.0.0.1:8080. The packaged Spring app serves React and the snapshot API from one origin. It reads snapshots at startup; restart after replacing prepared outputs. All referenced assets in that prepared folder are served locally; curate an approved subset before public hosting. Unknown asset/snapshot IDs are rejected. No GPU worker is required.

With the app running, `python3 api/verify.py` checks real snapshot/detail/assets and frontend delivery. For UI development, `npm run dev --prefix ui` proxies API/assets to port 8080. Current constant-baseline records visibly require inspection; they are not model classifications.

For a phone on the same trusted Wi-Fi, start with `--server.address=0.0.0.0` and open `http://<Mac-LAN-IP>:8080`. Obtain that IP with `ipconfig getifaddr en0`. This exposes the prepared gallery to reachable devices; public hosting still requires an approved asset subset. The Java package uses `controller`, `service`, `repository` and `dto` layers under `team.creditburners`.
