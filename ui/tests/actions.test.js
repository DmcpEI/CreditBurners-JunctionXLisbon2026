import test from 'node:test';
import assert from 'node:assert/strict';
import {isAlert, matchesAlertType} from '../src/features/snapshots/actions.js';

test('saved alerts distinguish shelf issues from defaults and mocks', () => {
  const assessed = {prediction_source:'saved', fallback_used:false, visibility:'clear', stock_level:'full', planogram_compliant:true};
  assert.equal(isAlert(assessed), false);
  for (const issue of [{stock_level:'empty'}, {stock_level:'half'}, {planogram_compliant:false}, {visibility:'occluded'}, {visibility:'unknown'}]) {
    assert.equal(isAlert({...assessed, ...issue}), true);
  }
  assert.equal(isAlert({...assessed, stock_level:'empty', fallback_used:true}), false);
  assert.equal(isAlert({...assessed, stock_level:'empty', prediction_source:'mock'}), false);
});

import {assessmentFacts, searchText} from '../src/features/snapshots/presentation.js';

test('stock and product mismatch remain visible together', () => {
  const area = {fallback_used:false, visibility:'clear', stock_level:'empty', planogram_compliant:false};
  assert.deepEqual(assessmentFacts(area).map(fact => fact.label), ['Empty','Product mismatch']);
  assert.deepEqual(assessmentFacts({...area,fallback_used:true}), []);
  assert.deepEqual(assessmentFacts({...area,visibility:'occluded'}), []);
  assert.deepEqual(assessmentFacts({...area,prediction_source:'mock'}), []);
  assert.equal(searchText('Maçã'),searchText('maca'));
});

test('a shelf with two issues appears in both relevant task filters', () => {
  const area = {prediction_source:'saved',fallback_used:false,visibility:'clear',stock_level:'empty',planogram_compliant:false};
  assert.equal(matchesAlertType(area,'Restock'),true);
  assert.equal(matchesAlertType(area,'Check product'),true);
  assert.equal(matchesAlertType(area,'Check stock'),false);
  assert.equal(matchesAlertType({...area,fallback_used:true},'Restock'),false);
});
