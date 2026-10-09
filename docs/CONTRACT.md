# Contract

Status: planned interface for the first implementation; no endpoints exist yet. Keep the scoring export separate from the richer presentation data. Member1 owns prediction semantics; Member2 owns API/UI integration. Coordinate changes before implementation.

## Endpoints

Core app: Spring serves the built React UI and these read-only routes from the same origin.

| Request | Response |
|---|---|
| `GET /api/snapshots` | Array of approved snapshot summaries: `snapshot_id`, `camera_id`, `image_file`, `captured_at`, `image_url` |
| `GET /api/snapshots/{snapshot_id}` | One full app snapshot in the format below; unknown/unpublished ID returns 404 |
| `GET /assets/{asset_id}` | An explicitly published image/crop; unknown/unpublished ID returns 404 |

The client filters by camera and orders by capture time for the small demo gallery. Only known IDs are accepted, never filesystem paths or remote image URLs. UI browsing must not trigger GPU inference.

Fresh inference is a separate stretch implementation. If built:
- `POST /api/analyses` accepts `{ "snapshot_id": "known-published-id" }` and returns 202 with `{ "job_id": "opaque-id", "status": "queued" }`.
- `GET /api/analyses/{job_id}` returns `job_id`, `status` (`queued`, `running`, `complete`, `failed`), `result` (app snapshot or null), and `error` (safe message or null). Invalid IDs return 404; full queue returns 429; unavailable worker returns 503 on creation.
- One persistent Python worker processes a bounded queue. Spring polls/serves job status. Specify the local worker handoff when implementing; the recorded demo does not depend on it.
- Completed fresh results have `prediction_source: "fresh"` and a new `run_id`. Do not overwrite the curated replay or silently return a saved result for a fresh request.
- Phone uploads are a further stretch; agree their multipart interface only after the gallery and fresh-analysis path work. Require one tray, expected product, bounded decoded image dimensions/size, generated filenames and temporary storage. Do not reuse a store area's geometry/history for an unrelated photo.

## Data formats

### Sensei export

Exactly `camera_id → image_file → area_id → prediction`:

```json
{
  "demo_camera": {
    "1700000000.jpg": {
      "demo_camera_1": {
        "planogram_compliant": true,
        "stock_level": "half",
        "stock_value": 0.5
      }
    }
  }
}
```

This is a synthetic format example, not a result. Real exports use the exact supplied IDs and filenames and cover every required image/area. `planogram_compliant` is a JSON boolean. `stock_level` is `empty`, `half` or `full`, paired with `stock_value` 0, 0.5 or 1 respectively. No UI metadata, probabilities, null predictions or omitted required areas in the scoring export. Model failure uses the evaluated deterministic fallback; the app separately discloses that fallback.

### App snapshot

Python writes app snapshots and evidence assets; Spring reads them for the core demo. One snapshot contains all areas of one camera image. Publish complete files atomically so the API never reads partial JSON.

```json
{
  "snapshot_id": "demo-001",
  "run_id": "illustrative-fixture",
  "camera_id": "demo_camera",
  "image_file": "1700000000.jpg",
  "captured_at": "2023-11-14T22:13:20Z",
  "processed_at": "2023-11-14T22:14:00Z",
  "prediction_source": "mock",
  "context_mode": "current_image_only",
  "image_url": "/assets/demo-image",
  "areas": [
    {
      "area_id": "demo_camera_1",
      "product_name": "Banana",
      "planogram_compliant": true,
      "stock_level": "half",
      "stock_value": 0.5,
      "visibility": "clear",
      "fallback_used": false,
      "crop_url": "/assets/demo-crop",
      "reference": null,
      "reason": "Illustrative mock: check whether this shelf needs restocking."
    }
  ]
}
```

- Example values and asset IDs above are synthetic and do not resolve yet. ISO 8601 timestamps include timezone; use original capture time, not processing time, for replay order.
- `prediction_source`: `saved`, `fresh` or `mock`. This describes how the displayed result was obtained, not whether its image is current. Always show a mock banner for `mock`.
- `context_mode`: `current_image_only`, `past_only` or `retrospective`. The last may use later frames and must be disclosed. Do not represent retrospective processing as live monitoring.
- `visibility`: `clear`, `occluded` or `unknown`. No trustworthy confidence percentage is required for the core UI.
- `reference`: null or `{ "crop_url": "/assets/known-reference", "captured_at": "2023-11-14T22:00:00Z" }`. A reference is not automatically a full/compliant shelf.
- `reason` must follow the actual prediction/evidence, with no invented counts, freshness diagnosis, monetary value or causal claims.
- Derive actions consistently: unclear visibility or `fallback_used` → inspect; otherwise empty → restock; mismatch → check product; half → check stock; otherwise OK. Retain both stock and compliance indicators even when one action is prioritised. Use this declared severity order, not an unsupported financial estimate.
- Optional staff acknowledgement is separate from the model prediction. Marking a task checked must not change stock/compliance or the Sensei export.
- Run identity links results to model, prompt and preprocessing settings retained with the ML output. Keep weights, real images, uploads and generated result files out of Git.

## Mocks

Use a small explicitly synthetic fixture covering empty, half, full, mismatch and occlusion so API/UI work can begin independently. It must use the same app format and `prediction_source: "mock"`; do not include it in measured evaluation or present it as model output.

Implementation checks: exact Sensei keys/types/value pairs, one complete snapshot served through API/UI, correct capture/reference timestamps, unavailable assets, and visible fallback/mock labels. `scripts/smoke_test.sh` remains a placeholder until these checks are implemented.
