import test from 'node:test';
import assert from 'node:assert/strict';
import {scrollToContent} from '../src/features/snapshots/scrollToContent.js';

test('opening evidence clears sticky controls and clamps near the page start',()=>{
 const controls={'.app-header':{position:'sticky',getBoundingClientRect:()=>({height:119})},'.study-toolbar':{position:'sticky',getBoundingClientRect:()=>({height:114})}};
 globalThis.document={querySelector:selector=>controls[selector]};
 globalThis.getComputedStyle=element=>element;
 let result;
 globalThis.window={scrollY:1000,scrollTo:options=>{result=options;}};
 scrollToContent({getBoundingClientRect:()=>({top:300})});
 assert.deepEqual(result,{top:1055,behavior:'instant'});
 controls['.app-header'].position='static';delete controls['.study-toolbar'];
 scrollToContent({getBoundingClientRect:()=>({top:300})});
 assert.equal(result.top,1288);
 window.scrollY=0;
 scrollToContent({getBoundingClientRect:()=>({top:5})});
 assert.equal(result.top,0);
});
