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

Five synthetic test methods pass, covering the nine stock payoff combinations, compliance penalties, missing-area penalty, expected-score choice, strict value/coverage checks, off-image masks, crop orientation, malformed geometry, ZIP metadata handling, preservation of prior output directories and single-token answer encoding checks.

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

Reproduce on knuth from the remote workspace:
```bash
/workspace/miniconda/envs/jx/bin/python -B -u -m ml.infer_sample data/qwen-sample-v1/sample.json --model /workspace/models/qwen3.8-27b --output data/qwen-sample-v1/results.json
```
Unchanged completed samples return from cache without loading the model. Use a different output filename for a deliberately changed prompt/model experiment.

Next: clarify empty/half and curtain annotation rules; compare a revised visibility/stock prompt on these failure cases plus unchanged controls. Add a verified mismatch case before trusting compliance. At this sample speed, 1,962 areas would take roughly 46 minutes, excluding transfer/preparation and variation in image processing; do not spend that run before checking the failure cases. API/UI and the full-dataset inference/export path remain untested.
