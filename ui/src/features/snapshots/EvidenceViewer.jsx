import React, {useEffect, useRef, useState} from 'react';
import Evidence from './Evidence';

export default function EvidenceViewer({cropUrl, cameraUrl, title, capturedAt}) {
  const dialog = useRef(null);
  const trigger = useRef(null);
  const stage = useRef(null);
  const [open, setOpen] = useState(false);
  const [view, setView] = useState('crop');
  const [zoom, setZoom] = useState(1);
  const changeZoom = amount => setZoom(value => Math.min(3, Math.max(1, value + amount)));
  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    dialog.current.showModal();
    return () => { document.body.style.overflow = previousOverflow; };
  }, [open]);
  useEffect(() => { stage.current?.scrollTo(0, 0); }, [view]);
  const close = () => {
    dialog.current?.close();
    setOpen(false);
    trigger.current?.focus({preventScroll: true});
  };
  return <>
    <button className="image-expand" ref={trigger} onClick={() => {setView('crop'); setZoom(1); setOpen(true);}}><span aria-hidden="true">⤢</span> Enlarge image</button>
    {open && <dialog ref={dialog} className="image-viewer" aria-labelledby="viewer-title" onCancel={event => {event.preventDefault(); close();}}
      onKeyDown={event => {if (event.key === '+' || event.key === '=') {event.preventDefault(); changeZoom(.5);} if (event.key === '-') {event.preventDefault(); changeZoom(-.5);}}}>
      <header className="viewer-header"><div><h2 id="viewer-title">{title}</h2><p>{capturedAt} · Recorded image</p></div><button className="viewer-close" onClick={close} aria-label="Close image viewer">Close <span aria-hidden="true">×</span></button></header>
      <div className="viewer-toolbar"><div className="viewer-tabs" role="group" aria-label="Image view"><button aria-pressed={view === 'crop'} onClick={() => {setView('crop'); setZoom(1);}}>Shelf crop</button><button aria-pressed={view === 'camera'} disabled={!cameraUrl} onClick={() => {setView('camera'); setZoom(1);}}>Full camera</button></div><div className="zoom-controls" role="group" aria-label="Image magnification"><button onClick={() => changeZoom(-.5)} disabled={zoom === 1} aria-label="Zoom out">−</button><output aria-live="polite">{Math.round(zoom * 100)}%</output><button onClick={() => changeZoom(.5)} disabled={zoom === 3} aria-label="Zoom in">+</button><button onClick={() => {setZoom(1); stage.current?.scrollTo(0,0);}}>Fit</button></div></div>
      <div className="viewer-stage" ref={stage} tabIndex={0} aria-label="Image. Scroll to explore when enlarged."><div className="viewer-canvas" style={{width: `${zoom * 100}%`, height: `${zoom * 100}%`}}><Evidence url={view === 'crop' ? cropUrl : cameraUrl} alt={view === 'crop' ? `${title}, shelf crop` : 'Full camera view for this recorded observation'}/></div></div>
      <p className="viewer-hint">Enlarge, then scroll to explore. Enlargement does not add image detail.</p>
    </dialog>}
  </>;
}
