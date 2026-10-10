import React, {useState} from 'react';
import {dateLabel, timeLabel} from './presentation';

export default function ObservationToolbar({browser,hideCamera=false}) {
  const {current, summaries, frames, position, mode, playing, selectCamera, selectFrame, toggleReplay, loading, reducedMotion, pauseReplay, storeView} = browser;
  const [expanded, setExpanded] = useState(false);
  const finishSelection = callback => { callback(); setExpanded(false); };
  const cameras = [...new Set(summaries.map(s => s.camera_id))];
  return <section className="observation-toolbar" aria-label="Choose a recorded observation">
    <button className="observation-toggle" aria-expanded={expanded} aria-controls="observation-fields" onClick={() => setExpanded(value => !value)}>
      <span><strong>{storeView ? 'Store overview' : current ? `Camera ${current.camera_id}` : 'Choose an observation'}{current && !storeView && <span className="capture-time"> · {timeLabel(current.captured_at)}</span>}</strong><small>{storeView ? `Latest recorded image · ${cameras.length} cameras` : `${current ? dateLabel(current.captured_at) : 'Recorded store images'} · Saved observation`}</small></span><span className="change-label">{expanded ? 'Close' : 'Change'}</span>
    </button>
    <div id="observation-fields" className={`picker-fields ${expanded ? 'expanded' : ''}`}>
    {!hideCamera && <div className="observation-picker">
      <label htmlFor="camera">Camera</label>
      <select id="camera" name="camera" value={storeView ? 'all' : current?.camera_id || ''} disabled={!cameras.length}
        onChange={e => finishSelection(() => selectCamera(e.target.value))}>
        {mode !== 'study' && <option value="all">All cameras · Store overview</option>}
        {!current && <option value="">Choose a camera</option>}
        {cameras.map(id => <option value={id} key={id}>Camera {id}</option>)}
      </select>
    </div>}
    {mode==='study' && <div className={`observation-picker time-picker ${mode !== 'study' ? 'store-time-picker' : ''}`} aria-hidden={mode !== 'study'}>
      <label htmlFor="capture">Recorded image</label>
      <select id="capture" name="capture" value={current?.snapshot_id || ''} disabled={!frames.length}
        onChange={e => finishSelection(() => selectFrame(e.target.value))}>
        {!current && <option value="">Choose an observation</option>}
        {frames.map((frame, i) => <option key={frame.snapshot_id} value={frame.snapshot_id}>
          {dateLabel(frame.captured_at)} · {timeLabel(frame.captured_at)}{i === frames.length - 1 ? ' · Latest recorded' : ''}
        </option>)}
      </select>
    </div>}
    <span className="recorded-note">{storeView ? 'Latest recorded image per camera' : 'Saved observation'}<br/><span>Not a live camera feed</span></span>
    </div>
    {mode === 'study' && <div className="replay-controls" onFocusCapture={pauseReplay}>
      <button className="button secondary" disabled={position <= 0 || loading} onClick={() => selectFrame(frames[position - 1].snapshot_id)}>Previous image</button>
      <button className="button primary" disabled={frames.length < 2 || loading || reducedMotion} onClick={toggleReplay}>{playing ? 'Pause replay' : 'Play the day'}</button>
      <button className="button secondary" disabled={position < 0 || position >= frames.length - 1 || loading} onClick={() => selectFrame(frames[position + 1].snapshot_id)}>Next image</button>
      <p>Image {Math.max(0, position + 1)} of {frames.length}. Frames are roughly an hour apart.{reducedMotion ? ' Use Previous and Next with reduced motion enabled.' : ''}</p>
    </div>}
  </section>;
}
