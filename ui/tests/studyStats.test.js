import test from 'node:test';
import assert from 'node:assert/strict';
import {studyStats} from '../src/features/snapshots/studyStats.js';
const frame=(time,level,patch={})=>({snapshot_id:time,captured_at:time,prediction_source:'saved',areas:[{area_id:'c_1',product_name:'Apple',stock_level:level,visibility:'clear',fallback_used:false,planogram_compliant:true,...patch}]});
test('study uses assessed observation denominators and preserves both stock and mismatch',()=>{
 const result=studyStats([frame('2025-06-27T11:00:00Z','empty',{planogram_compliant:false}),frame('2025-06-27T10:00:00Z','full')]);
 assert.equal(result.total,2);assert.equal(result.assessed,2);assert.equal(result.empty,1);assert.equal(result.mismatch,1);
 assert.equal(result.transitions.length,1);assert.equal(result.transitions[0].direction,'decrease');
});
test('unknown observations break transitions and demo/fallback data produce no metrics',()=>{
 const result=studyStats([frame('2025-06-27T10:00:00Z','full'),frame('2025-06-27T11:00:00Z','half',{visibility:'unknown'}),frame('2025-06-27T12:00:00Z','empty')]);
 assert.equal(result.assessed,2);assert.equal(result.unassessed,1);assert.equal(result.transitions.length,0);
 for(const data of [[{...frame('2025-06-27T10:00:00Z','empty'),prediction_source:'mock'}],[frame('2025-06-27T10:00:00Z','empty',{manual_preview:true})],[frame('2025-06-27T10:00:00Z','empty',{fallback_used:true})]])assert.equal(studyStats(data).assessed,0);
});
