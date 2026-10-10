import React from 'react';
import {fullTime,timeLabel} from './presentation';

const states=['empty','half','full','unknown'];
const label={empty:'Empty',half:'Half',full:'Full',unknown:'Unassessed'};
export default function StudyGraphs({stats,browser,preview}) {
  const cameras=new Map();
  browser.summaries.forEach(frame=>cameras.set(frame.camera_id,(cameras.get(frame.camera_id)||0)+1));
  const coverage=[...cameras].sort((a,b)=>b[1]-a[1] || String(a[0]).localeCompare(String(b[0])));
  const max=Math.max(1,...coverage.map(([,count])=>count));
  return <div className="study-graphs">
    <section className="study-chart"><header><span className="section-kicker">{preview?'Manual demo':'Saved assessments'}</span><h3>Stock distribution</h3><p>Area observations across this camera’s recorded images.</p></header>
      <div className="distribution-bars">{states.map(state=>{const count=state==='unknown'?stats.unassessed:stats[state];return <div className="distribution-row" key={state}><span>{label[state]}</span><div className="chart-track" aria-hidden="true"><i className={`chart-fill stock-${state}`} style={{width:`${stats.total?count/stats.total*100:0}%`}}/></div><strong>{count}<small>{stats.total?Math.round(count/stats.total*100):0}%</small></strong></div>;})}</div>
    </section>
    <section className="study-chart"><header><span className="section-kicker">{preview?'Manual demo':'Saved assessments'}</span><h3>Stock through the day</h3><p>Each bar is one capture. Tap it to explore that image; gaps are unobserved.</p></header>
      <div className="chart-legend">{states.map(state=><span key={state}><i className={`stock-${state}`}/>{label[state]}</span>)}</div>
      <div className="timeline-scroll" tabIndex={0} aria-label="Scrollable stock history"><div className="stock-timeline">{stats.series.map((point,index)=><button key={point.snapshot_id} aria-pressed={browser.location.snapshot===point.snapshot_id} onClick={()=>browser.selectFrame(point.snapshot_id)} aria-label={`${fullTime(point.captured_at)}: ${states.map(state=>`${point[state]} ${label[state].toLowerCase()}`).join(', ')}`}><span className="timeline-bar" aria-hidden="true">{states.map(state=><i key={state} className={`stock-${state}`} style={{height:`${point.total?point[state]/point.total*100:0}%`}}/>)}</span><strong>{timeLabel(point.captured_at)}</strong><small>Image {index+1}</small></button>)}</div></div>
    </section>
    <section className="study-chart coverage-chart"><header><span className="section-kicker">Actual image inventory</span><h3>Camera coverage</h3><p>{browser.summaries.length} recorded images across {coverage.length} cameras. More images does not mean more customer movement.</p></header><div className="coverage-bars">{coverage.map(([camera,count])=><button key={camera} aria-pressed={browser.current?.camera_id===camera} onClick={()=>browser.selectCamera(camera)} aria-label={`Camera ${camera}: ${count} images. Open camera history.`}><span>Camera {camera}</span><span className="chart-track" aria-hidden="true"><i className="chart-fill coverage-fill" style={{width:`${count/max*100}%`}}/></span><strong>{count}<small>images</small></strong></button>)}</div></section>
  </div>;
}
