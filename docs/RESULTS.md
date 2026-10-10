# Results

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
