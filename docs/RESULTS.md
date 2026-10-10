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

Four synthetic test methods pass, covering the nine stock payoff combinations, compliance penalties, missing-area penalty, expected-score choice, strict value/coverage checks, off-image masks, crop orientation, malformed geometry, ZIP metadata handling and preservation of prior output directories.

## How measured

- ZIP inventory and Pillow decoding; image filename timestamps and planogram counts.
- `python3 -m ml.prepare new_dataset_hackathon_junctionx_10_oct_2026_v2 --output data/prepared-v1` completed on all images.
- Inspected a 14-camera overview, first/middle/last frames on both curtain cameras, and selected crops with masks. Not every crop has been visually reviewed.
- `bash scripts/smoke_test.sh` runs the synthetic preparation/scoring checks. GPU inference and API/UI have not been tested by this command.

## Next experiment

Run the existing Qwen model on a small cross-camera sample, including curtains, genuinely empty areas, visible produce and clipped polygons. Keep predictions cached; compare with allowed human labels before claiming accuracy or choosing a confidence threshold. Confirm Sensei's annotation rule for closed curtains.
