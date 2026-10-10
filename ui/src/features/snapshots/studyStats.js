import {hasProductAssessment} from './assessmentMetadata.js';
export function studyStats(snapshots, {includePreview=false}={}) {
  const ordered = [...snapshots].sort((a,b)=>Date.parse(a.captured_at)-Date.parse(b.captured_at));
  let total=0, assessed=0, empty=0, half=0, full=0, mismatch=0,productAssessed=0;
  const transitions=[];
  const series=[];
  const shelves=new Map();
  const usable=(snapshot,area)=>!area.fallback_used && area.visibility === 'clear' && ['empty','half','full'].includes(area.stock_level) && (area.manual_preview ? includePreview : snapshot.prediction_source !== 'mock');
  const levels={empty:0,half:1,full:2};
  ordered.forEach((snapshot,index)=>{
    const previous=ordered[index-1];
    const point={snapshot_id:snapshot.snapshot_id,captured_at:snapshot.captured_at,empty:0,half:0,full:0,unknown:0,total:snapshot.areas.length};
    series.push(point);
    snapshot.areas.forEach(area=>{
      total++;
      if (!usable(snapshot,area)) {point.unknown++;return;}
      point[area.stock_level]++;
      assessed++;
      const key=`${snapshot.camera_id}:${area.area_id}`;
      const shelf=shelves.get(key) || {area_id:area.area_id,product_name:area.product_name,assessed:0,empty:0,half:0};
      shelf.assessed++;
      if(area.stock_level==='empty' || area.stock_level==='half') {
        shelf[area.stock_level]++;
        shelf.snapshot_id=snapshot.snapshot_id;
        shelf.captured_at=snapshot.captured_at;
      }
      shelves.set(key,shelf);
      if(area.stock_level==='empty')empty++;
      if(area.stock_level==='half')half++;
      if(area.stock_level==='full')full++;
      if(hasProductAssessment(snapshot)) {productAssessed++;if(!area.planogram_compliant)mismatch++;}
      const before=previous?.areas.find(item=>item.area_id===area.area_id);
      if(!before || !usable(previous,before) || before.stock_level===area.stock_level) return;
      transitions.push({area_id:area.area_id,product_name:area.product_name,from:before.stock_level,to:area.stock_level,
        direction:levels[area.stock_level]>levels[before.stock_level]?'increase':'decrease',
        before_at:previous.captured_at,captured_at:snapshot.captured_at,snapshot_id:snapshot.snapshot_id});
    });
  });
  const attentionShelves=[...shelves.values()].filter(shelf=>shelf.empty+shelf.half>0).sort((a,b)=>(b.empty+b.half)/b.assessed-(a.empty+a.half)/a.assessed || b.empty-a.empty || a.area_id.localeCompare(b.area_id));
  return {attentionShelves,total,assessed,unassessed:total-assessed,empty,half,full,mismatch,productAssessed,transitions,series};
}
