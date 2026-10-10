import React, {useState} from 'react';
import geometry from 'virtual:shelf-geometry';
import {assessmentFacts, productLabel, shelfLabel, statusLabel} from './presentation';

export default function CameraMap({snapshot, selected, onSelect}) {
  const [dimensions, setDimensions] = useState(null);
  const [failed, setFailed] = useState(null);
  const [hovered, setHovered] = useState(null);
  const position = snapshot.areas.findIndex(area => area.area_id === selected);
  const highlighted = snapshot.areas.find(area => area.area_id === hovered || (!hovered && area.area_id === selected));
  const polygons = geometry[snapshot.camera_id] || {};
  const selectAdjacent = offset => onSelect(snapshot.areas[position + offset].area_id);
  return <section className="camera-map" aria-label="Interactive shelf map">
    <div className="map-heading"><div><h3>Explore this camera</h3><p>Tap a shelf to switch the details below.</p></div><span>{position + 1} / {snapshot.areas.length}</span></div>
    <div className="map-photo">
      {failed === snapshot.image_url ? <p className="image-missing">Camera image unavailable. Use the shelf controls below.</p> : <img key={snapshot.image_url} src={snapshot.image_url} alt={`Full recorded camera ${snapshot.camera_id}; select a shelf using the outlined areas`} onLoad={e => setDimensions({url:snapshot.image_url,width:e.currentTarget.naturalWidth,height:e.currentTarget.naturalHeight})} onError={() => setFailed(snapshot.image_url)}/>}
      {dimensions?.url === snapshot.image_url && failed !== snapshot.image_url && <svg viewBox={`0 0 ${dimensions.width} ${dimensions.height}`} aria-label="Select a shelf" className="map-overlay">
        {snapshot.areas.filter(area => polygons[area.area_id]).map(area => <polygon data-stock={assessmentFacts(area).length ? area.stock_level : undefined} key={area.area_id} points={polygons[area.area_id].map(point => point.join(',')).join(' ')} className={area.area_id === selected ? 'map-region selected' : 'map-region'} role="button" tabIndex={0} aria-label={`${shelfLabel(area)}, expected ${productLabel(area.product_name)}, ${statusLabel(area)}`} aria-pressed={selected === area.area_id} onMouseEnter={() => setHovered(area.area_id)} onMouseLeave={() => setHovered(null)} onFocus={() => setHovered(area.area_id)} onBlur={() => setHovered(null)} onClick={() => {setHovered(null); onSelect(area.area_id);}} onKeyDown={event => {if(event.key==='Enter'||event.key===' ') {event.preventDefault(); setHovered(null); onSelect(area.area_id);}}}><title>{shelfLabel(area)} · {productLabel(area.product_name)}</title></polygon>)}
      </svg>}
    </div>
    <div className="map-caption" aria-live="polite">{highlighted ? `${shelfLabel(highlighted)} · ${productLabel(highlighted.product_name)}` : 'Choose a shelf'}</div>
    <div className="map-shelves" aria-label="All shelves in this camera">{snapshot.areas.map(area=><button key={area.area_id} data-stock={assessmentFacts(area).length ? area.stock_level : undefined} aria-pressed={selected===area.area_id} onClick={()=>onSelect(area.area_id)}><strong>{productLabel(area.product_name)}</strong><span>{shelfLabel(area)} · {statusLabel(area)}</span></button>)}</div>
    <div className="map-navigation"><button disabled={position <= 0} onClick={() => selectAdjacent(-1)}>← Previous shelf</button><label><span className="sr-only">Choose shelf</span><select value={selected} onChange={event => onSelect(event.target.value)}>{snapshot.areas.map(area => <option key={area.area_id} value={area.area_id}>{shelfLabel(area)} · {productLabel(area.product_name)}</option>)}</select></label><button disabled={position >= snapshot.areas.length - 1} onClick={() => selectAdjacent(1)}>Next shelf →</button></div>
  </section>;
}
