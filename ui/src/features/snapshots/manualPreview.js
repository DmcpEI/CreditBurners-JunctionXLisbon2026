// Explicit UI-only fixture; never written to model outputs or submission files.
export function manualPreview(snapshot) {
  if (!snapshot) return snapshot;
  return {...snapshot, prediction_source:'mock', areas:snapshot.areas.map(area => ({
    ...area, visibility:'clear', fallback_used:false,
    manual_preview:true, reference:null,
    reason:'Manual UI demonstration. The original baseline stock and product values are preserved for preview; they are not assessments of the photo.'
  }))};
}
