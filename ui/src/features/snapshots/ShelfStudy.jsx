import React, {useMemo} from 'react';
import english from '../../../../ml/products_en.json';
import {fullTime, productLabel, shelfLabel, timeLabel} from './presentation';
import {byHour, observations, rank, shelfEvents, summary} from './insights';
import {manualPreview} from './manualPreview';
import ObservationToolbar from './ObservationToolbar';

const category = name => english[name] || productLabel(name);
const title = value => value.charAt(0).toLocaleUpperCase() + value.slice(1);
const pct = value => `${Math.round(value * 100)}%`;
const duration = minutes => minutes < 60 ? `${Math.round(minutes)} min` : `${Math.floor(minutes / 60)} h ${String(Math.round(minutes % 60)).padStart(2, '0')} min`;
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
const hourLabel = hour => `${String(hour).padStart(2, '0')}:00`;

// Shelf study: one recorded day, studied for the whole store, one camera (zone) or one product.
export default function ShelfStudy({browser, onOpen}) {
  const {studySnapshots, studyLoading, studyError, frames, location, navigate, current, retry} = browser;
  const preview = location.demo === '1';
  const all = useMemo(() => observations(preview ? studySnapshots.map(manualPreview) : studySnapshots, {category, includePreview: preview}), [studySnapshots, preview]);
  const products = useMemo(() => [...new Set(all.map(o => o.category))].sort(), [all]);
  const cameras = useMemo(() => [...new Set(all.map(o => o.camera_id))].sort(), [all]);
  const scope = ['camera', 'product'].includes(location.study) ? location.study : 'store';
  const product = products.includes(location.product) ? location.product : products[0];
  const camera = current?.camera_id;
  const obs = scope === 'camera' ? all.filter(o => o.camera_id === camera) : scope === 'product' ? all.filter(o => o.category === product) : all;
  const stats = useMemo(() => summary(obs), [obs]);
  const {changes, spells} = useMemo(() => shelfEvents(obs), [obs]);
  const latestOf = id => [...browser.summaries].filter(s => s.camera_id === id).at(-1)?.snapshot_id;
  const goCamera = id => navigate({study: 'camera', snapshot: latestOf(id), area: null});
  const goProduct = name => navigate({study: 'product', product: name, area: null});
  const subject = scope === 'store' ? 'the whole store' : scope === 'camera' ? `camera ${camera}` : title(product || '');

  if (studyLoading && !studySnapshots.length) return <p role="status" className="study-note">Loading the recorded day…</p>;
  if (studyError) return <div className="error-state" role="alert"><p>{studyError}</p><button className="button secondary" onClick={retry}>Retry</button></div>;
  return <section className="study-content overview-content" aria-label="Shelf study">
    <div className="study-scope">
      <div className="filters" role="group" aria-label="Study scope">{[['store', 'Whole store'], ['camera', 'Camera'], ['product', 'Product']].map(([id, label]) =>
        <button key={id} aria-pressed={scope === id} onClick={() => id === 'camera' ? goCamera(camera || cameras[0]) : navigate({study: id === 'store' ? null : id, area: null})}>{label}</button>)}</div>
      {scope === 'camera' && <label className="study-select"><span>Camera</span><select value={camera || ''} onChange={event => goCamera(event.target.value)}>{cameras.map(id => <option key={id} value={id}>Camera {id}</option>)}</select></label>}
      {scope === 'product' && <label className="study-select"><span>Product</span><select value={product || ''} onChange={event => goProduct(event.target.value)}>{products.map(name => <option key={name} value={name}>{title(name)}</option>)}</select></label>}
    </div>
    {preview && <p className="study-note"><strong>Demo values.</strong> Manual statuses on real photos, not model predictions. <button className="button secondary" onClick={() => navigate({demo: '0'}, true)}>Show model results</button></p>}

    <div className="study-metrics">
      <div><strong>{pct(stats.low)}</strong><span>of checks empty or half</span><small>{stats.n} shelf checks · {subject}</small></div>
      <div><strong>{stats.medianRefill === null ? '—' : duration(stats.medianRefill)}</strong><span>median wait, empty → refilled</span><small>{plural(stats.refilled, 'refill')}{stats.stillEmpty ? ` · ${stats.stillEmpty} not refilled by the last image` : ''}</small></div>
      <div><strong>{stats.changes}</strong><span>lasting stock changes</span><small>sales and restocks, flicker removed</small></div>
    </div>

    <HourChart hours={byHour(obs)} scope={scope} frames={frames} browser={browser}/>

    <div className="study-lists">
      {scope === 'store' && <>
        <RankList title="Products most often low" note="Share of checks empty or half. Candidates for more space or more frequent refills (or displayed half-full by design: check the photos). Tap to study the product."
          rows={rank(all, 'category').filter(r => r.n >= 13).slice(0, 6).map(r => ({...r, name: title(r.key), sub: plural(new Set(all.filter(o => o.category === r.key).map(o => o.area_id)).size, 'shelf').replace('shelfs', 'shelves'), onClick: () => goProduct(r.key)}))}/>
        <RankList title="Products rarely low" note="Almost always full. Their space may exceed what they sell; check before giving them more."
          rows={rank(all, 'category').filter(r => r.n >= 13).reverse().slice(0, 5).map(r => ({...r, name: title(r.key), sub: plural(new Set(all.filter(o => o.category === r.key).map(o => o.area_id)).size, 'shelf').replace('shelfs', 'shelves'), onClick: () => goProduct(r.key)}))}/>
        <ActivityList changes={changes} cameras={cameras} onPick={goCamera}/>
      </>}
      {scope !== 'store' && <RankList title={scope === 'camera' ? 'Shelves most often low' : 'Where it runs low'} note={`Share of checks empty or half. Tap to see the latest low image.${rank(obs, 'area_id').some(r => !r.low) ? ` ${plural(rank(obs, 'area_id').filter(r => !r.low).length, 'shelf').replace('shelfs', 'shelves')} never low.` : ''}`}
        rows={rank(obs, 'area_id').filter(r => r.low).map(r => ({...r, name: productLabel(r.first.product_name), sub: `${shelfLabel(r.first)} · Camera ${r.first.camera_id}`,
          onClick: r.latest_low ? () => onOpen({snapshot_id: r.latest_low.snapshot_id, area_id: r.key}) : null}))}/>}
      <RefillList spells={spells} onOpen={onOpen}/>
    </div>

    {scope === 'camera' && <section className="study-archive"><h3>Browse this camera's images</h3>
      <div className="study-frame-choice" aria-label="Selected study image"><button aria-label="Previous image" disabled={browser.position <= 0} onClick={() => browser.selectFrame(frames[browser.position - 1].snapshot_id)}>←</button><div><span>Image {browser.position + 1} of {frames.length}</span><strong>{current && fullTime(current.captured_at)}</strong></div><button aria-label="Next image" disabled={browser.position < 0 || browser.position >= frames.length - 1} onClick={() => browser.selectFrame(frames[browser.position + 1].snapshot_id)}>→</button></div>
      <ObservationToolbar browser={browser} hideCamera/></section>}
    <p className="study-note">One recorded day (27 June 2025), about one image per camera per hour. Stock levels are model estimates (about 88% right on our labelled shelves); a change counts unless the next image goes straight back. These figures show availability and replenishment, not sales.</p>
  </section>;
}

function HourChart({hours, scope, frames, browser}) {
  const usable = hours.slice(1).filter(h => h.n >= Math.max(...hours.map(x => x.n)) / 2);  // first image = overnight state
  const full = h => h.full / h.n;
  const best = usable.reduce((a, b) => full(b) > full(a) ? b : a, usable[0]);
  const worst = usable.reduce((a, b) => full(b) < full(a) ? b : a, usable[0]);
  const frameAt = hour => frames.find(f => new Date(f.captured_at).getHours() === hour);
  return <section className="study-chart study-hours active-chart"><header><span className="section-kicker">Stock by hour</span>
    <h3>When shelves run low</h3>
    {best && <p>Fullest around {hourLabel(best.hour)} ({pct(full(best))} full). Lowest around {hourLabel(worst.hour)} ({pct(full(worst))} full){hours[0] && hours[0] !== worst ? `; the first image (${hourLabel(hours[0].hour)}) starts at ${pct(hours[0].empty / hours[0].n)} empty` : ''}.{scope === 'camera' ? ' Tap an hour to open that image.' : ''}</p>}</header>
    <div className="chart-legend">{['empty', 'half', 'full'].map(state => <span key={state}><i className={`stock-${state}`}/>{title(state)}</span>)}</div>
    <div className="timeline-scroll" tabIndex={0} aria-label="Stock share by hour"><div className="stock-timeline">{hours.map(h => {
      const bar = <><span className="timeline-bar" aria-hidden="true">{['empty', 'half', 'full'].map(state => <i key={state} className={`stock-${state}`} style={{height: `${h[state] / h.n * 100}%`}}/>)}</span><strong>{hourLabel(h.hour)}</strong><small>{pct((h.empty + h.half) / h.n)} low</small></>;
      const label = `${hourLabel(h.hour)}: ${h.empty} empty, ${h.half} half, ${h.full} full`;
      const frame = scope === 'camera' && frameAt(h.hour);
      return frame ? <button key={h.hour} aria-label={label} aria-pressed={browser.location.snapshot === frame.snapshot_id} onClick={() => browser.selectFrame(frame.snapshot_id)}>{bar}</button>
        : <div key={h.hour} className="timeline-col" role="img" aria-label={label}>{bar}</div>;
    })}</div></div>
  </section>;
}

function Track({parts}) {
  return <span className="attention-track" aria-hidden="true">{parts.map(([cls, share]) => <i key={cls} className={cls} style={{width: `${share * 100}%`}}/>)}</span>;
}

function RankList({title: heading, note, rows}) {
  if (!rows.length) return null;
  return <section className="study-attention"><h3>{heading}</h3><p>{note}</p><ul>{rows.map(r => <li key={r.key}>
    <button disabled={!r.onClick} onClick={r.onClick || undefined}><div><strong>{r.name}</strong><span>{r.sub}</span></div>
      <Track parts={[['stock-empty', r.empty / r.n], ['stock-half', r.half / r.n]]}/>
      <span className="attention-count">{pct(r.low)} low<small>{r.empty} empty · {r.half} half · {r.n} checks</small></span></button></li>)}</ul></section>;
}

function ActivityList({changes, cameras, onPick}) {
  const counts = cameras.map(id => ({id, n: changes.filter(c => c.camera_id === id).length})).sort((a, b) => b.n - a.n);
  const max = Math.max(1, ...counts.map(c => c.n));
  const quiet = counts.slice(-3).reverse();
  return <section className="study-attention"><h3>Where stock moves most</h3><p>Lasting stock changes per camera zone (sales and restocks). Quietest: {quiet.map(c => `camera ${c.id} (${c.n})`).join(', ')}. Tap to study the zone.</p><ul>{counts.slice(0, 6).map(c => <li key={c.id}>
    <button onClick={() => onPick(c.id)}><div><strong>Camera {c.id}</strong><span>{plural(new Set(changes.filter(x => x.camera_id === c.id).map(x => x.area_id)).size, 'shelf').replace('shelfs', 'shelves')} changed</span></div>
      <Track parts={[['activity', c.n / max]]}/><span className="attention-count">{c.n} changes</span></button></li>)}</ul></section>;
}

function RefillList({spells, onOpen}) {
  const rows = spells.map(s => ({...s, wait: s.minutes ?? (s.open_until - s.t) / 60000})).sort((a, b) => b.wait - a.wait).slice(0, 6);
  if (!rows.length) return <section className="study-attention"><h3>Slowest refills</h3><p>No shelf went empty during the day here.</p></section>;
  const max = Math.max(...rows.map(r => r.wait));
  return <section className="study-attention"><h3>Slowest refills</h3><p>How long shelves stayed empty after running out. Each hour empty is a possible lost sale. Tap to see the empty shelf.</p><ul>{rows.map(r => <li key={`${r.area_id}:${r.t}`}>
    <button onClick={() => onOpen({snapshot_id: r.snapshot_id, area_id: r.area_id})}><div><strong>{productLabel(r.product_name)}</strong><span>{shelfLabel(r)} · Camera {r.camera_id} · empty from {timeLabel(r.t)}</span></div>
      <Track parts={[['stock-empty', r.wait / max]]}/><span className="attention-count">{r.minutes === null ? `${duration(r.wait)}+` : duration(r.wait)}<small>{r.minutes === null ? `still empty at ${timeLabel(r.open_until)}` : 'until refilled'}</small></span></button></li>)}</ul></section>;
}
