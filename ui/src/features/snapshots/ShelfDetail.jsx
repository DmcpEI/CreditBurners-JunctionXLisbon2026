import React, {useEffect, useRef} from 'react';
import Evidence from './Evidence';
import AssessmentBadges from './AssessmentBadges';
import CameraMap from './CameraMap';
import EvidenceViewer from './EvidenceViewer';
import {scrollToContent} from './scrollToContent';
import {fullTime, productLabel, shelfLabel, statusClass, statusLabel, taskDescription} from './presentation';

export default function ShelfDetail({snapshot, area, onBack, onSelectArea,cameraFirst=false}) {
  const heading = useRef(null);
  const detail=useRef(null);
  useEffect(() => {
    if (!area) return;
    if (detail.current) detail.current.scrollTop=0;
    heading.current?.focus({preventScroll:true});
    scrollToContent(detail.current);
  }, [area?.area_id,cameraFirst]);
  if (!area) return <aside className="detail-placeholder"><span className="placeholder-mark" aria-hidden="true">↗</span><h2>A closer look</h2><p>Choose a shelf from the checklist to see its image, suggested action and supporting evidence.</p></aside>;
  const position = snapshot.areas.findIndex(item => item.area_id === area.area_id);
  return <section className="shelf-detail" ref={detail} tabIndex={0} aria-labelledby="detail-title">
    <h1 className="sr-only mobile-detail-title">Shelf evidence</h1>
    <button className="back-button" onClick={onBack}><span aria-hidden="true">←</span> Back to shelves</button>
    <div className="detail-heading"><p className="shelf-location">{shelfLabel(area)} · Camera {snapshot.camera_id}</p><h2 id="detail-title" tabIndex={-1} ref={heading}>{productLabel(area.product_name)}</h2><span className={`status ${statusClass(area)}`}>{statusLabel(area)}</span></div>
    <div className="mobile-assessment"><strong>{statusLabel(area)}</strong><span>Captured {fullTime(snapshot.captured_at)}</span></div>
    <p className="detail-guidance">{taskDescription(area)}</p><AssessmentBadges area={{...area, prediction_source:snapshot.prediction_source}} productIssuesOnly/>{area.product_assessed===false && <p className="detail-limitation">Product match has not been checked.</p>}{cameraFirst && <CameraMap snapshot={snapshot} selected={area.area_id} onSelect={onSelectArea}/>}<figure className="crop-evidence"><Evidence url={area.crop_url} alt={`Observed crop of ${area.product_name}, ${shelfLabel(area)}, camera ${snapshot.camera_id}`}/><figcaption><span>Captured {fullTime(snapshot.captured_at)}</span><EvidenceViewer key={`${snapshot.snapshot_id}:${area.area_id}`} cropUrl={area.crop_url} cameraUrl={snapshot.image_url} title={`${productLabel(area.product_name)} · ${shelfLabel(area)}`} capturedAt={fullTime(snapshot.captured_at)}/></figcaption></figure>
    {!cameraFirst && <CameraMap snapshot={snapshot} selected={area.area_id} onSelect={onSelectArea}/>}
    <nav className="mobile-shelf-nav" aria-label="Browse shelves in this camera"><button disabled={position <= 0} onClick={() => onSelectArea(snapshot.areas[position - 1].area_id)}>← Previous</button><span>{position + 1} / {snapshot.areas.length}</span><button disabled={position >= snapshot.areas.length - 1} onClick={() => onSelectArea(snapshot.areas[position + 1].area_id)}>Next →</button></nav>
  </section>;
}
