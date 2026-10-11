import React from 'react';
import Evidence from './Evidence';
import LiveTime from './LiveTime';
import {action, isAlert} from './actions';

export default function StoreCameras({snapshots,onOpen}) {
  return <section className="store-cameras overview-content" aria-labelledby="camera-title"><div className="study-heading"><h2 id="camera-title">Around your store</h2><p>Simulated live view: the latest image from each camera, most urgent first. Tap a camera to see its shelves.</p></div><div className="camera-shortcuts"><a href="#shelves-title">Browse all shelves ↓</a></div><ul id="latest-camera-gallery" className="camera-gallery">{byUrgency(snapshots).map(snapshot=><li key={snapshot.camera_id}><button disabled={!snapshot.areas.length} onClick={()=>onOpen({snapshot_id:snapshot.snapshot_id,area_id:snapshot.areas[0]?.area_id,focus:'camera',camera:snapshot.camera_id})}><Evidence url={snapshot.image_url} alt={`Latest recorded camera ${snapshot.camera_id}`} thumbnail/><strong>Camera {snapshot.camera_id}</strong><LiveTime at={snapshot.captured_at}/><CameraTasks areas={snapshot.areas}/><span>{snapshot.areas.length} shelves · Explore ↗</span></button></li>)}</ul></section>;
}

const counts = areas => {
  const tasks = areas.filter(isAlert);
  return {urgent: tasks.filter(a => action(a) === 'Restock').length, soon: tasks.filter(a => action(a) === 'Check stock').length};
};
// Cameras with the most urgent restocks first, so the gallery also says where to walk.
const byUrgency = snapshots => [...snapshots].sort((a, b) => {
  const x = counts(a.areas), y = counts(b.areas);
  return y.urgent - x.urgent || y.soon - x.soon || a.camera_id.localeCompare(b.camera_id);
});
function CameraTasks({areas}) {
  const {urgent, soon} = counts(areas);
  if (!urgent && !soon) return <span className="camera-tasks none">No restock tasks</span>;
  return <span className="camera-tasks">{urgent > 0 && <b className="urgent">{urgent} urgent</b>}{soon > 0 && <b className="low">{soon} restock soon</b>}</span>;
}
