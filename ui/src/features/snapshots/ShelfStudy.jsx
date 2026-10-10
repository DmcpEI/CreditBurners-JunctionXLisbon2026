import React, {useMemo} from 'react';
import {fullTime, productLabel, shelfLabel} from './presentation';
import {studyStats} from './studyStats';
import {manualPreview} from './manualPreview';
import StudyGraphs from './StudyGraphs';
import ObservationToolbar from './ObservationToolbar';

export default function ShelfStudy({browser, onOpen}) {
  const {studySnapshots,studyLoading,studyError,frames,location,selectFrame,retry}=browser;
  const preview=location.demo === '1';
  const stats=useMemo(()=>studyStats(preview ? studySnapshots.map(manualPreview) : studySnapshots,{includePreview:preview}),[studySnapshots,preview]);
  const selected=stats.series.find(point=>point.snapshot_id===location.snapshot);
  return <section className="study-content overview-content" aria-label="Historical shelf study">
    {studyLoading ? <p role="status" className="study-note">Loading camera history…</p> : studyError ? <div className="error-state" role="alert"><p>{studyError}</p><button className="button secondary" onClick={retry}>Retry history</button></div> : <>
      <div className="study-frame-choice" aria-label="Selected study image"><button aria-label="Previous study image" disabled={browser.position<=0} onClick={()=>selectFrame(frames[browser.position-1].snapshot_id)}>←</button><div><span>Selected image · {browser.position+1} of {frames.length}</span><strong>{browser.current && fullTime(browser.current.captured_at)}</strong></div><button aria-label="Next study image" disabled={browser.position<0 || browser.position>=frames.length-1} onClick={()=>selectFrame(frames[browser.position+1].snapshot_id)}>→</button></div>
      <p className="study-image-summary">{selected?.total || 0} shelves in this image{selected?.unknown ? ` · ${selected.unknown} not assessed` : ''}{preview?' · Demo values':''}</p>
      <div className="study-metrics"><div><strong>{selected?.empty || 0}</strong><span>Restock first</span></div><div><strong>{selected?.half || 0}</strong><span>Check restock</span></div><div><strong>{selected?.full || 0}</strong><span>No restock needed</span></div></div>
      {!stats.assessed && <p className="study-note">No usable assessments in original records. Enable demo graphs to explore the existing baseline values; the image archive remains available.</p>}
      {preview && <p className="study-note"><strong>Demo graphs · Manual baseline values</strong><br/>Supplied stock/compliance values are preserved across images. These graphs demonstrate the interface; they do not measure shelf conditions or sales. <button className="button secondary" onClick={()=>browser.navigate({demo:'0'},true)}>Show original records</button></p>}
      {studySnapshots.some(s=>s.context_mode==='retrospective') && <p className="study-note">Some predictions use later images as context. This is retrospective analysis, not historical live monitoring.</p>}
      <StudyGraphs stats={stats} selected={selected} browser={browser} preview={preview}/>
      {stats.transitions.length > 0 && <section className="study-changes"><h3>Observed stock changes</h3><ul>{stats.transitions.map(item=><li key={`${item.snapshot_id}:${item.area_id}`}><button onClick={()=>onOpen(item)}><strong>{productLabel(item.product_name)} · {shelfLabel(item)}</strong><span>{item.from} → {item.to} · observed {item.direction}</span><small>{fullTime(item.before_at)} → {fullTime(item.captured_at)}</small><span>Open evidence ↗</span></button></li>)}</ul></section>}
    </>}
    <section className="study-archive"><h3>Recorded images</h3><ObservationToolbar browser={browser} hideCamera/></section>
    <p className="study-note">Saved predictions on recorded images. Gaps are unobserved; these graphs do not measure sales or customer traffic.</p>
  </section>;
}
