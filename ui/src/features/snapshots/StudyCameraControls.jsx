import React from 'react';

export default function StudyCameraControls({browser}) {
  const {summaries,current,selectCamera}=browser;
  const cameras=[...new Set(summaries.map(frame=>frame.camera_id))].sort((a,b)=>String(a).localeCompare(String(b)));
  return <section className="store-camera-picker study-camera-picker" aria-label="Dashboard camera">
    <label htmlFor="study-camera"><span>Camera</span><select id="study-camera" value={current?.camera_id || ''} disabled={!cameras.length} onChange={event=>selectCamera(event.target.value)}>{!current && <option value="">Choose a camera</option>}{cameras.map(camera=><option key={camera} value={camera}>Camera {camera}</option>)}</select></label>
  </section>;
}
