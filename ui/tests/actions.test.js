import test from 'node:test';
import assert from 'node:assert/strict';
import {isAlert} from '../src/features/snapshots/actions.js';

test('saved alerts distinguish shelf issues from defaults and mocks', () => {
  const assessed = {prediction_source:'saved', fallback_used:false, visibility:'clear', stock_level:'full', planogram_compliant:true};
  assert.equal(isAlert(assessed), false);
  for (const issue of [{stock_level:'empty'}, {stock_level:'half'}, {planogram_compliant:false}, {visibility:'occluded'}, {visibility:'unknown'}]) {
    assert.equal(isAlert({...assessed, ...issue}), true);
  }
  assert.equal(isAlert({...assessed, stock_level:'empty', fallback_used:true}), false);
  assert.equal(isAlert({...assessed, stock_level:'empty', prediction_source:'mock'}), false);
});
