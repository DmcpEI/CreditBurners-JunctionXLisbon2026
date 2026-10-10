import React from 'react';

export default function StudyCameraControls({browser}) {
  const {summaries,current,frames,selectCamera,studyLoading}=browser;
  const cameras=[...new Set(summaries.map(frame=>frame.camera_id))].sort((a,b)=>String(a).localeCompare(String(b)));
  const position=cameras.indexOf(current?.camera_id);
  return <section className="study-camera-controls" aria-label="Dashboard camera">
    <button aria-label="Previous camera" disabled={position<=0} onClick={()=>selectCamera(cameras[position-1])}>←</button>
    <div><label htmlFor="study-camera">Camera · {Math.max(0,position+1)} of {cameras.length}</label><select id="study-camera" value={current?.camera_id || ''} disabled={!cameras.length} onChange={event=>selectCamera(event.target.value)}>{!current && <option value="">Choose a camera</option>}{cameras.map(camera=><option key={camera} value={camera}>Camera {camera}</option>)}</select></div>
    <button aria-label="Next camera" disabled={position<0 || position>=cameras.length-1} onClick={()=>selectCamera(cameras[position+1])}>→</button>
    <span className="study-camera-caption" role="status">{studyLoading?'Loading history…':`${frames.length} recorded images · Saved stock predictions`}</span>
  </section>;
}
