// These published runs fix compliance to true; it is not a product assessment.
export const hasProductAssessment = snapshot => snapshot.product_check != null
  ? snapshot.product_check === 'model'
  : !/stockonly|alwayscompliant|emptycheck/.test(snapshot.run_id || '');
// Confirmed exclusions from our labelling protocol; this is not a general curtain detector.
const coveredFrames = new Set(['6383_1751001156', '6386_1751001156']);
export function withAssessmentMetadata(snapshot) {
  return snapshot && {...snapshot,areas:snapshot.areas.map(area=>({...area,
    product_assessed:hasProductAssessment(snapshot),
    ...(coveredFrames.has(snapshot.snapshot_id) ? {visibility:'occluded', reason:'Stock is hidden by a closed refrigeration curtain.'} : {})}))};
}
