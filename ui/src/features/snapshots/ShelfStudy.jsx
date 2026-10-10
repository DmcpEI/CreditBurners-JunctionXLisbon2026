import React, {useMemo} from 'react';
import Evidence from './Evidence';
import {fullTime, productLabel, shelfLabel} from './presentation';
import {studyStats} from './studyStats';

export default function ShelfStudy({browser, onOpen}) {
  const {studySnapshots,studyLoading,studyError,frames,location,selectFrame,retry}=browser;
  const stats=useMemo(()=>studyStats(studySnapshots),[studySnapshots]);
  return <section className="study-content overview-content" aria-label="Historical shelf study">
    <div className="study-heading"><h2>Study the recorded day</h2><p>Compare shelf conditions across captures. These images do not measure purchases or customer traffic.</p></div>
    {studyLoading ? <p role="status" className="study-note">Loading camera history…</p> : studyError ? <div className="error-state" role="alert"><p>{studyError}</p><button className="button secondary" onClick={retry}>Retry history</button></div> : <>
      <div className="study-metrics"><div><strong>{stats.assessed} / {stats.total}</strong><span>Clear assessed area observations</span></div><div><strong>{stats.assessed ? `${stats.empty} / ${stats.assessed}` : '—'}</strong><span>Observed empty</span></div><div><strong>{stats.assessed ? `${stats.mismatch} / ${stats.assessed}` : '—'}</strong><span>Observed product mismatches</span></div></div>
      {!stats.assessed && <p className="study-note">Study summaries await real model assessments. Baselines, manual demo statuses and obstructed observations are excluded. The image archive remains available.</p>}
      {stats.assessed > 0 && <p className="study-note">Counts refer to sampled observations, not separate incidents or hours empty. Gaps between frames are unobserved; predictions are not ground truth.</p>}
      {studySnapshots.some(s=>s.context_mode==='retrospective') && <p className="study-note">Some predictions use later images as context. This is retrospective analysis, not historical live monitoring.</p>}
      {stats.transitions.length > 0 && <section className="study-changes"><h3>Observed stock changes</h3><ul>{stats.transitions.map(item=><li key={`${item.snapshot_id}:${item.area_id}`}><button onClick={()=>onOpen(item)}><strong>{productLabel(item.product_name)} · {shelfLabel(item)}</strong><span>{item.from} → {item.to} · observed {item.direction}</span><small>{fullTime(item.before_at)} → {fullTime(item.captured_at)}</small><span>Open evidence ↗</span></button></li>)}</ul></section>}
    </>}
    <div className="study-heading"><h3>Camera image archive</h3><p>{frames.length} images, oldest to newest. Select an image, then explore its shelves below.</p></div>
    <ul className="frame-archive">{frames.map((frame,index)=><li key={frame.snapshot_id}><button aria-pressed={location.snapshot===frame.snapshot_id} onClick={()=>selectFrame(frame.snapshot_id)}><Evidence url={frame.image_url} alt={`Camera ${frame.camera_id}, captured ${fullTime(frame.captured_at)}`} thumbnail/><span>Image {index+1}{index===frames.length-1?' · Latest':''}</span><strong>{fullTime(frame.captured_at)}</strong><span>{location.snapshot===frame.snapshot_id?'Selected image':'Explore image ↗'}</span></button></li>)}</ul>
  </section>;
}
