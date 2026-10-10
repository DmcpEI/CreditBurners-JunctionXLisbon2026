// These published runs fix compliance to true; it is not a product assessment.
export const hasProductAssessment = snapshot => !/stockonly|alwayscompliant|emptycheck/.test(snapshot.run_id || '');
export function withAssessmentMetadata(snapshot) {
  return snapshot && {...snapshot,areas:snapshot.areas.map(area=>({...area,product_assessed:hasProductAssessment(snapshot)}))};
}
