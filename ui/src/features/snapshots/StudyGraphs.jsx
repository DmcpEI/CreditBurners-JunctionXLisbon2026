import React from 'react';
import {fullTime,timeLabel} from './presentation';

const states=['empty','half','full','unknown'];
const label={empty:'Empty',half:'Half',full:'Full',unknown:'Unassessed'};
export default function StudyGraphs({stats,selected,browser,preview}) {
  const charts=[['timeline','Through the day'],['stock','This image']];
  const active=charts.some(([id])=>id===browser.location.chart)?browser.location.chart:'timeline';
  const cameras=new Map();
  browser.summaries.forEach(frame=>cameras.set(frame.camera_id,(cameras.get(frame.camera_id)||0)+1));
  const coverage=[...cameras].sort((a,b)=>b[1]-a[1] || String(a[0]).localeCompare(String(b[0])));
  const max=Math.max(1,...coverage.map(([,count])=>count));
  return <div className="study-graphs">
    <div className="study-chart-switch" role="group" aria-label="Choose dashboard graph">{charts.map(([id,title])=><button key={id} aria-pressed={active===id} aria-controls={`study-chart-${id}`} onClick={()=>browser.navigate({chart:id},true)}>{title}</button>)}</div>
    <section id="study-chart-stock" className={`study-chart ${active==='stock'?'active-chart':''}`}><header><span className="section-kicker">{preview?'Manual demo':'Saved assessments'}</span><h3>Stock in this image</h3><p>{selected?.total || 0} shelves · {selected && fullTime(selected.captured_at)}</p></header>
      <div className="distribution-bars">{states.map(state=>{const count=selected?.[state] || 0;const total=selected?.total || 0;return <div className="distribution-row" key={state}><span>{label[state]}</span><div className="chart-track" aria-hidden="true"><i className={`chart-fill stock-${state}`} style={{width:`${total?count/total*100:0}%`}}/></div><strong>{count}<small>{total?Math.round(count/total*100):0}%</small></strong></div>;})}</div>
    </section>
    <section id="study-chart-timeline" className={`study-chart ${active==='timeline'?'active-chart':''}`}><header><span className="section-kicker">{preview?'Manual demo':'Saved assessments'}</span><h3>Stock through the day</h3><p>Each bar is one capture. Tap it to explore that image; gaps are unobserved.</p></header>
      <div className="chart-legend">{states.map(state=><span key={state}><i className={`stock-${state}`}/>{label[state]}</span>)}</div>
      <div className="timeline-scroll" tabIndex={0} aria-label="Scrollable stock history"><div className="stock-timeline">{stats.series.map((point,index)=><button key={point.snapshot_id} aria-pressed={browser.location.snapshot===point.snapshot_id} onClick={()=>browser.selectFrame(point.snapshot_id)} aria-label={`${fullTime(point.captured_at)}: ${states.map(state=>`${point[state]} ${label[state].toLowerCase()}`).join(', ')}`}><span className="timeline-bar" aria-hidden="true">{states.map(state=><i key={state} className={`stock-${state}`} style={{height:`${point.total?point[state]/point.total*100:0}%`}}/>)}</span><strong>{timeLabel(point.captured_at)}</strong><small>Image {index+1}</small></button>)}</div></div>
    </section>
    <details className="study-coverage"><summary>Dataset coverage <span>{browser.summaries.length} images · {coverage.length} cameras</span></summary><section id="study-chart-coverage" className="study-chart coverage-chart"><header><span className="section-kicker">Actual image inventory</span><h3>Camera coverage</h3><p>{browser.summaries.length} recorded images across {coverage.length} cameras. More images does not mean more customer movement.</p></header><div className="coverage-bars">{coverage.map(([camera,count])=><button key={camera} aria-pressed={browser.current?.camera_id===camera} onClick={()=>{browser.selectCamera(camera);browser.navigate({chart:'stock'},true);document.querySelector('.study-toolbar')?.scrollIntoView({block:'start',behavior:browser.reducedMotion?'instant':'smooth'});}} aria-label={`Camera ${camera}: ${count} images. Open camera history.`}><span>Camera {camera}</span><span className="chart-track" aria-hidden="true"><i className="chart-fill coverage-fill" style={{width:`${count/max*100}%`}}/></span><strong>{count}<small>images</small></strong></button>)}</div></section></details>
  </div>;
}
