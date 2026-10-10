import React, {useEffect, useRef} from 'react';
import Evidence from './Evidence';
import CameraMap from './CameraMap';
import EvidenceViewer from './EvidenceViewer';
import {action} from './actions';
import {fullTime, productLabel, shelfLabel, statusClass, statusLabel, taskDescription} from './presentation';

export default function ShelfDetail({snapshot, area, onBack, onSelectArea}) {
  const heading = useRef(null);
  useEffect(() => {
    if (area) {
      heading.current?.focus({preventScroll: true});
      if (window.matchMedia('(max-width: 760px)').matches) window.scrollTo({top: 0, behavior: 'instant'});
    }
  }, [area?.area_id]);
  if (!area) return <aside className="detail-placeholder"><span className="placeholder-mark" aria-hidden="true">↗</span><h2>A closer look</h2><p>Choose a shelf from the checklist to see its image, suggested action and supporting evidence.</p></aside>;
  const fallback = area.fallback_used;
  const inspect = action(area) === 'Inspect';
  return <section className="shelf-detail" aria-labelledby="detail-title">
    <h1 className="sr-only mobile-detail-title">Shelf evidence</h1>
    <button className="back-button" onClick={onBack}><span aria-hidden="true">←</span> Back to shelves</button>
    <div className="detail-heading"><p className="shelf-location">{shelfLabel(area)} · Camera {snapshot.camera_id}</p><h2 id="detail-title" tabIndex={-1} ref={heading}>{productLabel(area.product_name)}</h2><span className={`status ${statusClass(area)}`}>{statusLabel(area)}</span></div>
    <CameraMap snapshot={snapshot} selected={area.area_id} onSelect={onSelectArea}/><figure className="crop-evidence"><Evidence url={area.crop_url} alt={`Observed crop of ${area.product_name}, ${shelfLabel(area)}, camera ${snapshot.camera_id}`}/><figcaption><span>Captured {fullTime(snapshot.captured_at)}</span><EvidenceViewer key={`${snapshot.snapshot_id}:${area.area_id}`} cropUrl={area.crop_url} cameraUrl={snapshot.image_url} title={`${productLabel(area.product_name)} · ${shelfLabel(area)}`} capturedAt={fullTime(snapshot.captured_at)}/></figcaption></figure>
    <div className={`suggestion ${statusClass(area)}`}><h3>{fallback ? 'Assessment unavailable' : inspect ? 'Check the shelf before acting' : statusLabel(area)}</h3><p>{taskDescription(area)}</p>{fallback && <p className="suggestion-note">The photo is available, but the supplied results use default values. They do not describe the stock visible in this image.</p>}</div>
    <section className="observation-facts" aria-label="Observation assessment"><h3>{fallback ? 'What we know' : 'What was observed'}</h3><dl><div><dt>Stock</dt><dd>{fallback ? 'Not assessed' : area.stock_level}</dd></div><div><dt>Expected product · planogram</dt><dd>{productLabel(area.product_name)}</dd></div><div><dt>Product match</dt><dd>{fallback ? 'Not assessed' : area.planogram_compliant ? 'Matches planogram' : 'Product mismatch'}</dd></div><div><dt>Visibility</dt><dd>{area.visibility === 'clear' ? 'Clear view' : area.visibility === 'occluded' ? 'Obstructed' : 'Not assessed'}</dd></div></dl></section>
    <details className="evidence-disclosure"><summary>Why this task?</summary><p>{area.reason || 'No additional explanation was supplied.'}</p></details>
    {area.reference && <section className="reference-evidence"><h3>Reference image</h3><p>Captured {fullTime(area.reference.captured_at)}. This observation is not necessarily full or compliant.</p><Evidence url={area.reference.crop_url} alt={`Reference observation of ${area.product_name}`}/></section>}
    <details className="evidence-disclosure context-image"><summary>See the full camera image</summary><Evidence url={snapshot.image_url} alt={`Full recorded view from camera ${snapshot.camera_id}`}/></details>
    <details className="evidence-disclosure"><summary>Observation details</summary><dl><div><dt>Area ID</dt><dd>{area.area_id}</dd></div><div><dt>Product label</dt><dd>{area.product_name}</dd></div><div><dt>Source</dt><dd>{snapshot.prediction_source}</dd></div><div><dt>Processed</dt><dd>{fullTime(snapshot.processed_at)}</dd></div><div><dt>Run</dt><dd>{snapshot.run_id}</dd></div><div><dt>Context</dt><dd>{snapshot.context_mode.replaceAll('_', ' ')}</dd></div></dl></details>
  </section>;
}
