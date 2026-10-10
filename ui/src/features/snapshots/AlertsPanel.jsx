import React, {useEffect, useRef, useState} from 'react';
import Evidence from './Evidence';
import {rank} from './actions';
import {fullTime, productLabel, shelfLabel, statusLabel, statusClass, taskDescription} from './presentation';

export default function AlertsPanel({areas, unavailable, busy, onOpen}) {
  const [open, setOpen] = useState(false);
  const dialog = useRef(null);
  const trigger = useRef(null);
  useEffect(() => {
    if (!open) return;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    dialog.current.showModal();
    return () => { document.body.style.overflow = overflow; };
  }, [open]);
  const close = () => {dialog.current?.close(); setOpen(false); trigger.current?.focus({preventScroll:true});};
  return <>
    <button ref={trigger} className="alerts-trigger" disabled={busy} aria-label={`Open recorded alerts${areas.length ? `, ${areas.length} shelves` : ''}`} onClick={() => setOpen(true)}>
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Z"/><path d="M9 21h6"/></svg>
      {areas.length > 0 && <span className="alerts-count">{areas.length}</span>}
    </button>
    {open && <dialog ref={dialog} className="alerts-panel" aria-labelledby="alerts-title" onCancel={event => {event.preventDefault(); close();}}>
      <header className="alerts-heading"><div><p>Recorded observations</p><h2 id="alerts-title">Shelf alerts</h2></div><button className="viewer-close" aria-label="Close alerts" onClick={close}>Close ×</button></header>
      <p className="alerts-intro">{areas.length ? `${areas.length} shelves to check in the selected observations. These are saved assessments, not live notifications.` : unavailable ? 'No reliable assessments available for these shelves yet.' : 'No issues were flagged in the selected observations.'}</p>
      {unavailable > 0 && <p className="alerts-unassessed">{unavailable} shelves without a reliable assessment. They are not counted as confirmed alerts.</p>}
      {areas.length > 0 ? <ul className="alerts-list">{[...areas].sort((a,b)=>rank(a)-rank(b)).map((area, index) => <li style={{'--alert-delay': `${Math.min(index, 5) * 45}ms`}} key={`${area.snapshot_id}:${area.area_id}`}><button className={`alert-card ${statusClass(area)}`} onClick={() => {close(); onOpen(area);}}><div className="alert-card-top"><Evidence className="alert-thumbnail" url={area.crop_url} alt="" thumbnail/><div><span className="alert-action"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M12 3 2 21h20L12 3Z"/><path d="M12 9v5m0 3v1"/></svg>{statusLabel(area)}</span><strong>{productLabel(area.product_name)}</strong><span>{shelfLabel(area)} · Camera {area.camera_id}</span></div></div><span>{fullTime(area.captured_at)}</span><p>{taskDescription(area)}</p><span className="alert-open"><span>View shelf</span><span aria-hidden="true">↗</span></span></button></li>)}</ul> : <div className="alerts-empty"><span aria-hidden="true">—</span><h3>{unavailable ? 'Images ready. Assessments pending.' : 'Nothing to review here.'}</h3><p>{unavailable ? 'You can still browse the photos and inspect each shelf.' : 'Choose another camera or recorded time to review its results.'}</p><button className="button primary" onClick={close}>Browse shelves</button></div>}
    </dialog>}
  </>;
}
