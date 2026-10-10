import React, {useState} from 'react';
import Evidence from './Evidence';
import {fullTime} from './presentation';

export default function StoreCameras({snapshots,onOpen}) {
  const [expanded, setExpanded] = useState(false);
  return <section className="store-cameras overview-content" aria-labelledby="camera-title"><div className="study-heading"><h2 id="camera-title">Latest camera images</h2><p>One latest recorded image per camera. Capture times differ; this is not a live feed.</p></div><div className="camera-shortcuts"><a href="#shelves-title">Browse all shelves ↓</a><button aria-expanded={expanded} aria-controls="latest-camera-gallery" onClick={()=>setExpanded(value=>!value)}>{expanded ? 'Show fewer cameras' : 'Show all cameras'}</button></div><ul id="latest-camera-gallery" className={`camera-gallery ${expanded ? 'expanded' : ''}`}>{snapshots.map(snapshot=><li key={snapshot.camera_id}><button disabled={!snapshot.areas.length} onClick={()=>onOpen({snapshot_id:snapshot.snapshot_id,area_id:snapshot.areas[0]?.area_id})}><Evidence url={snapshot.image_url} alt={`Latest recorded camera ${snapshot.camera_id}`} thumbnail/><strong>Camera {snapshot.camera_id}</strong><span>{fullTime(snapshot.captured_at)}</span><span>{snapshot.areas.length} shelves · Explore ↗</span></button></li>)}</ul></section>;
}
