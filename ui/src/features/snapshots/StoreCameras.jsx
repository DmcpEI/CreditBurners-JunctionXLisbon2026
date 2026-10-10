import React from 'react';
import Evidence from './Evidence';
import {fullTime} from './presentation';

export default function StoreCameras({snapshots,onOpen}) {
  return <section className="store-cameras overview-content" aria-labelledby="camera-title"><div className="study-heading"><h2 id="camera-title">Around your store</h2><p>Choose a camera and tap a shelf. Latest recorded images, not a live feed.</p></div><div className="camera-shortcuts"><a href="#shelves-title">Browse all shelves ↓</a></div><ul id="latest-camera-gallery" className="camera-gallery">{snapshots.map(snapshot=><li key={snapshot.camera_id}><button disabled={!snapshot.areas.length} onClick={()=>onOpen({snapshot_id:snapshot.snapshot_id,area_id:snapshot.areas[0]?.area_id,focus:'camera'})}><Evidence url={snapshot.image_url} alt={`Latest recorded camera ${snapshot.camera_id}`} thumbnail/><strong>Camera {snapshot.camera_id}</strong><span>{fullTime(snapshot.captured_at)}</span><span>{snapshot.areas.length} shelves · Explore ↗</span></button></li>)}</ul></section>;
}
