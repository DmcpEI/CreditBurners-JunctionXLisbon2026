import React, {useState} from 'react';
import geometry from 'virtual:shelf-geometry';
import {assessmentFacts,productLabel,shelfLabel,statusLabel,timeLabel} from './presentation';

export default function CameraPreview({snapshots,onOpen}) {
  const [index,setIndex]=useState(0);
  const snapshot=snapshots[index%snapshots.length];
  if(!snapshot) return null;
  const polygons=geometry[snapshot.camera_id] || {};
  const open=area=>onOpen({snapshot_id:snapshot.snapshot_id,area_id:area.area_id,focus:'camera',camera:snapshot.camera_id});
  return <figure className="hero-camera"><div className="hero-camera-photo"><img src={snapshot.image_url} alt={`Latest recorded image from camera ${snapshot.camera_id}`}/><svg className="map-overlay" viewBox="0 0 1280 720" aria-label="Open a shelf in this camera">{snapshot.areas.filter(area=>polygons[area.area_id]).map(area=><polygon key={area.area_id} className="map-region" data-stock={assessmentFacts(area).length ? area.stock_level : undefined} points={polygons[area.area_id].map(point=>point.join(',')).join(' ')} role="button" tabIndex={0} aria-label={`${productLabel(area.product_name)}, ${shelfLabel(area)}, ${statusLabel(area)}`} onClick={()=>open(area)} onKeyDown={event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();open(area);}}}/>)}</svg></div><figcaption><button className="hero-camera-open" disabled={!snapshot.areas.length} onClick={()=>open(snapshot.areas[0])}><strong>Camera {snapshot.camera_id} <span aria-hidden="true">↗</span></strong><span>Last seen {timeLabel(snapshot.captured_at)}</span></button><div className="hero-camera-controls"><button aria-label="Previous preview camera" disabled={snapshots.length<2} onClick={()=>setIndex(value=>(value-1+snapshots.length)%snapshots.length)}>←</button><button aria-label="Next preview camera" disabled={snapshots.length<2} onClick={()=>setIndex(value=>(value+1)%snapshots.length)}>→</button></div></figcaption></figure>;
}
