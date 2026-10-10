export function studyStats(snapshots) {
  const ordered = [...snapshots].sort((a,b)=>Date.parse(a.captured_at)-Date.parse(b.captured_at));
  let total=0, assessed=0, empty=0, mismatch=0;
  const transitions=[];
  const usable=(snapshot,area)=>snapshot.prediction_source !== 'mock' && !area.manual_preview && !area.fallback_used && area.visibility === 'clear';
  const levels={empty:0,half:1,full:2};
  ordered.forEach((snapshot,index)=>{
    const previous=ordered[index-1];
    snapshot.areas.forEach(area=>{
      total++;
      if (!usable(snapshot,area)) return;
      assessed++;
      if(area.stock_level==='empty')empty++;
      if(!area.planogram_compliant)mismatch++;
      const before=previous?.areas.find(item=>item.area_id===area.area_id);
      if(!before || !usable(previous,before) || before.stock_level===area.stock_level) return;
      transitions.push({area_id:area.area_id,product_name:area.product_name,from:before.stock_level,to:area.stock_level,
        direction:levels[area.stock_level]>levels[before.stock_level]?'increase':'decrease',
        before_at:previous.captured_at,captured_at:snapshot.captured_at,snapshot_id:snapshot.snapshot_id});
    });
  });
  return {total,assessed,unassessed:total-assessed,empty,mismatch,transitions};
}
