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

import {manualPreview} from '../src/features/snapshots/manualPreview.js';
test('manual preview is explicit and does not mutate saved records', () => {
  const original={prediction_source:'saved',areas:Array.from({length:4},(_,i)=>({area_id:`a${i}`,fallback_used:true,stock_level:'half'}))};
  const preview=manualPreview(original);
  assert.equal(original.areas[0].stock_level,'half');
  assert.equal(original.prediction_source,'saved');
  assert.equal(preview.prediction_source,'mock');
  assert.equal(preview.areas.filter(isAlert).length,4);
  assert.deepEqual(preview.areas.map(a=>a.stock_level),original.areas.map(a=>a.stock_level));
  assert.equal(preview.areas.every(a=>a.manual_preview),true);
});

import {withAssessmentMetadata} from '../src/features/snapshots/assessmentMetadata.js';
test('stock-only presentation does not claim verified product matches',()=>{
 const original={run_id:'qwen3.8-27b-stockonly-half020-full-v1',areas:[{stock_level:'full',visibility:'clear',fallback_used:false,planogram_compliant:true}]};
 const area=withAssessmentMetadata(original).areas[0];
 assert.deepEqual(assessmentFacts(area).map(fact=>fact.label),['Full','Product not assessed']);
 assert.equal(original.areas[0].product_assessed,undefined);
});
