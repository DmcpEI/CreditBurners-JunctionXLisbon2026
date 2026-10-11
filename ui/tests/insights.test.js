import test from 'node:test';
import assert from 'node:assert/strict';
import {byHour, observations, rank, shelfEvents, summary} from '../src/features/snapshots/insights.js';
import {withAssessmentMetadata} from '../src/features/snapshots/assessmentMetadata.js';
import {matchesProduct, storeHour, fullTime} from '../src/features/snapshots/presentation.js';

const snap = (hour, levels, patch = {}) => ({snapshot_id: `c_${hour}`, camera_id: 'c', captured_at: `2025-06-27T${String(hour).padStart(2, '0')}:00:00+01:00`, prediction_source: 'saved',
  areas: Object.entries(levels).map(([area, level]) => ({area_id: area, product_name: area === 'c_1' ? 'MACA FUJI' : 'BANANA', stock_level: level, visibility: 'clear', fallback_used: false, ...patch}))});

test('unusable observations are excluded; preview only when asked', () => {
  const data = [snap(8, {c_1: 'full'}), snap(9, {c_1: 'empty'}, {fallback_used: true}), snap(10, {c_1: 'half'}, {visibility: 'unknown'}),
    {...snap(11, {c_1: 'empty'}), prediction_source: 'mock'}, snap(12, {c_1: 'half'}, {manual_preview: true})];
  assert.equal(observations(data).length, 1);
  assert.equal(observations(data, {includePreview: true}).length, 2);
});

test('A-B-A flicker is ignored; overnight empties are not refill spells', () => {
  const levels = ['empty', 'full', 'half', 'full', 'empty', 'empty', 'full', 'full'];  // 06:00..13:00
  const obs = observations(levels.map((level, i) => snap(6 + i, {c_1: level})));
  const {changes, spells} = shelfEvents(obs);
  // 08:00 half is flicker (09:00 is full again); the last image cannot be confirmed
  assert.deepEqual(changes.map(c => [c.hour, c.from, c.level]), [[7, 0, 2], [10, 2, 0], [12, 0, 2]]);
  assert.equal(spells.length, 1);
  assert.equal(spells[0].hour, 10);
  assert.equal(spells[0].minutes, 120);
  const s = summary(obs);
  assert.equal(s.n, 8);
  assert.equal(s.medianRefill, 120);
  assert.equal(s.stillEmpty, 0);
});

test('hour profile and ranking by share of low observations', () => {
  const obs = observations([snap(9, {c_1: 'full', c_2: 'empty'}), snap(10, {c_1: 'half', c_2: 'empty'})]);
  assert.deepEqual(byHour(obs).map(h => [h.hour, h.empty, h.half, h.full]), [[9, 1, 0, 1], [10, 1, 1, 0]]);
  const ranked = rank(obs, 'area_id');
  assert.deepEqual(ranked.map(r => [r.key, r.low]), [['c_2', 1], ['c_1', 0.5]]);
  assert.equal(ranked[1].latest_low.hour, 10);
});

test('confirmed curtains never become stock evidence, including in manual previews', () => {
  for (const snapshot_id of ['6383_1751001156', '6386_1751001156']) {
    const original = {...snap(6, {c_1: 'full'}), snapshot_id};
    const assessed = withAssessmentMetadata(original);
    assert.equal(assessed.areas[0].visibility, 'occluded');
    assert.equal(original.areas[0].visibility, 'clear');
    assert.equal(observations([original]).length, 0);
    assert.equal(observations([{...original, areas: original.areas.map(a => ({...a, manual_preview: true}))}], {includePreview: true}).length, 0);
  }
  assert.equal(observations([snap(7, {c_1:'full'})]).length, 1);
});

test('English and Portuguese searches find the same shelf without losing ID search', () => {
  const area = {area_id:'6462_1', product_name:'MORANGO EMB. 500 GR'};
  for (const query of ['strawberry', 'Morango', '6462_1', 'shelf 1']) assert.ok(matchesProduct(area, query, 'strawberry'));
  assert.equal(matchesProduct(area, 'banana', 'strawberry'), false);
});

test('store hours follow Lisbon daylight saving and midnight regardless of viewer timezone', () => {
  assert.equal(storeHour('2025-06-27T23:30:00Z'), 0);
  assert.equal(storeHour('2025-12-27T23:30:00Z'), 23);
  assert.equal(observations([{...snap(6, {c_1:'full'}), captured_at:'2025-06-27T05:00:00Z'}])[0].hour, 6);
  assert.match(fullTime('2025-06-27T23:30:00Z'), /28/);
});
