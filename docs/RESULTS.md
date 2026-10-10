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


## Integrated crop-presence pipeline — 10 October 2026

Default staged inference now uses crop+mask for presence while retaining context+crop+mask for visibility, fill and compliance. Tested 20 observations across all 14 cameras: previous 12 cases plus one mid-day first-area observation from each of eight previously unseen cameras. This sample was chosen for coverage, not class balance.

- Reused 36 identical question answers from v2 and the presence comparison; ran only 34 new questions. Per-question cache keys include model path, exact prompt and ordered image bytes. Keep model contents/environment fixed when reusing this cache; use a separate cache after replacing model weights or changing inference settings.
- Sparse bananas now pass presence and are classified half; product match is uncertain, so the diagnostic action is inspect. Both closed curtains still stop after visibility; the open cabbage tray remains inspectable.
- All eight added crops are classified visible and populated, consistent with provisional visual inspection. Stock agrees with six non-ambiguous provisional visual judgments; lemons and potatoes remain ambiguous half/full cases and were not assigned a reference level.
- Product identification is now the main observed weakness: both new apple examples and the packaged strawberry example receive mismatch answers despite visually plausible product-type matches. Apricot identity is uncertain on visual review. These are suspected false alarms, not authoritative cultivar/brand labels.
- New complete four-stage examples took approximately 1.68–1.71 seconds each; cached examples' near-zero times are cache retrieval, not inference throughput.

Inputs/results: `data/qwen-integrated-v3/{sample,results}.json`; the per-question seed cache is `answers.json`. Provisional visual review: `visual-review.json`, authored by the assistant, not a human or Sensei, covering eight new cases plus sparse bananas. These checks are for development, not supervised training/calibration. The eight new crops were reviewed before reading their model outputs. A team member should review uncertain labels; never silently turn these into official truth.

Remote workspace: `/workspace/jx/sensei-integrated-v3`:
```bash
/workspace/miniconda/envs/jx/bin/python -B -u -m ml.infer_sample data/qwen-integrated-v3/sample.json --model /workspace/models/qwen3.8-27b --output data/qwen-integrated-v3/results.json --answer-cache data/qwen-integrated-v3/answers.json
```

Eight synthetic test methods pass, including input selection, expected-product isolation and cache identity. API/UI and full-dataset submission remain separate unfinished steps. Next: isolate product-match false alarms using the same input-comparison approach, preserving visibility gates and cached answers.

Clarification from the supplied brief: shared train/test images have no annotations; only the hidden final validation has `annotations.json`. The JSON shown in the PDF illustrates its format, not labels for all supplied images. We are not waiting for more labels: proceed with the planogram, image inspection and a small provisional development reference set. The final competition score will come from Sensei at the end as planned.


## Crop-only product matching and integration — 10 October 2026

Ran 16 visible/populated cases using crop+mask for compliance, keeping the question and expected product unchanged and removing camera context. Compared with cached v3 answers. Added four explicitly synthetic wrong-product expectations (banana→tomato, tomato→banana, lemon→strawberry, cabbage→lemon) to test obvious rejection; these are not real shelf mismatches.

All 16 actual expected-product queries returned match. The two apple examples and packaged strawberry example no longer trigger the suspected false alarms; sparse bananas move from uncertain to match. Apricot also moves from mismatch to match, but its exact identity remains unverified by a human. All four synthetic wrong expectations returned mismatch. This is a development comparison, not a claim of 100% real-world compliance accuracy; subtle cultivar and mixed-product errors are still untested.

Default pipeline now uses crop+mask for both presence and compliance, with camera context retained for visibility and stock. Integrated all 20 original examples by replaying exact prompt/image cache matches through the stage logic, without repeating inference. The sparse banana tray now yields half/match and `check_stock`; both curtains still yield `inspect`. Eight synthetic test methods pass.

Experiment inputs/results: `data/qwen-compliance-ablation/{sample,results}.json`; remote workspace `/workspace/jx/sensei-compliance-ablation`. Diagnostic flag: `--crop-compliance-only` (mutually exclusive with `--crop-presence-only`). Integrated cached replay: `data/qwen-integrated-v4/replay-results.json`, with input manifest and seeded question cache alongside it. This replay is a diagnostic artifact, not the competition export or app snapshots. No new live end-to-end latency measurement was made for the final combination.

Next delivery: complete scoring/app exports with explicit fallbacks for unobservable cases, then broader visual review and a full dataset run. Keep ambiguous half/full examples uncertain in development references. No dependence on receiving training labels; final scoring follows Sensei's end-of-event validation.


## Human review set v1 — 10 October 2026

Built `data/human-review-v1/`: 60 observations, 32 development and 28 held-out, spanning all 14 cameras. Each camera contributes first/last frames of one development area and one previously untested area; four development areas also contribute middle frames. Splits are area-disjoint. Held-out areas exclude every area in the existing `data/qwen*/sample.json` manifests at creation. This is a coverage-oriented sample, not a random estimate of production accuracy; it does not deliberately include verified real mismatches.

Set ID: `93b9d1c2db63ec53`. The manifest fixes image/crop hashes, sampling split and provisional labeling definitions. Generated artifacts stay local. No model answers are shown or prefilled. Human labels have **not** been collected yet. Stock choices are empty/half/full or uncertain; blocked observations and empty-area compliance remain null for local review, not fabricated competition labels. Product labels refer to visibly identifiable type, not unverifiable cultivar/brand/origin.

Build with `python3 -m ml.label_set --output data/human-review-v1` (refuses overwriting an existing set). Open via `python3 -m http.server 8765 --bind 127.0.0.1 --directory data/human-review-v1`, then visit `http://127.0.0.1:8765`. Enter reviewer, label each item, and Save & next. Draft JSON exports provide backups; freeze/export becomes available when all items are reviewed. Frozen references are locked in that browser and any later corrections must be a separate explicit revision. Save downloaded labels under the local review directory before scoring. Browser storage is local to that browser/origin; use the same browser and port when resuming.

Keep holdout results out of prompt tuning; compare development results first. Score stock and compliance separately on definite labels and report the number excluded as uncertain. Do not use partially labelled references as an official competition score. Review is for evaluation, not fine-tuning or fitting a calibration model.

Nine Python test methods pass, including deterministic area-disjoint sampling and exclusion of exposed areas. Browser checks cover blank initial answers, blocked-view gating, save/reload, null export values and mobile layout. Synthetic browser test labels are isolated and are not part of the review dataset.


## Confirmed evaluation scope — 10 October 2026

User relayed organiser guidance: create our own empty/half/full annotations; closed-white-curtain images should be discarded from task evaluation because the final validation will show products unobstructed. No additional training labels are expected. This resolves the earlier uncertainty about including curtained shelves in the benchmark.

Preserve the in-progress review set and browser labels. Mark confirmed curtain examples Blocked / curtain; their stock and compliance remain null, and they must be excluded from stock/product metric denominators and any calibration, with exclusion counts reported. Retain images as provenance/optional robustness examples rather than deleting source data. No automatic broad white-colour filter: packaging and pale shelves are valid inputs. Final submission still requires every requested area, including fallback predictions if the visibility model is mistaken.

Knuth use is authorised for the project. No server environment or hosting changes were made in this update. Next priority is collecting the human stock reference and testing visible-shelf errors, not further curtain tuning.


## Assisted annotation — 10 October 2026

At the user's request, visually inspected all 60 review-set crops and created local `data/human-review-v1/suggestions.json`: 60 assistant-authored suggestions, 4 blocked curtains, 22 attention flags. These are not Qwen outputs or confirmed human labels. Suggestions include visibility, stock, product match, reasons and candidate stock classes where ambiguous. Existing manifest/set ID and saved browser reviews are preserved. Browser-saved human answers override suggestions. Navigation alone does not confirm a suggestion; Save & next does. Exports retain suggestion provenance separately from the human review. This supersedes the earlier prediction-blind review procedure: assisted labels can introduce anchoring bias. Holdout area separation remains, but this is no longer blind human annotation.

Sensei advice relayed by the user is to choose predictions by points gained/lost. Under a hypothetical 50/50 empty/half belief, expected stock score is -0.5 for predicting empty versus -1 for half. This supports a conservative submission choice; it does not establish the true stock class or those probabilities. Three sparse examples (1, 4, 8) have tentative empty suggestions with explicit empty/half uncertainty, despite visible produce. The reviewer should resolve or retain uncertainty rather than treating cost-aware guesses as definite evaluation truth. No empirical confidence probabilities were assigned.

The labeling UI allows product match independently of stock level for visible views, so a conservative empty choice with a few visible products need not erase product identity. Genuinely empty or blocked areas still use unknown product match. Suggestions remain excluded from completed-label counts until explicitly saved. Reviewers may choose uncertain instead of the suggested class. No model fitting or evaluation against these unconfirmed suggestions was performed.
