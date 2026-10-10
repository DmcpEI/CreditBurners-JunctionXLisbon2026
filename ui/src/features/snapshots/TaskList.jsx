import React, {useMemo, useRef} from 'react';
import Evidence from './Evidence';
import AssessmentBadges from './AssessmentBadges';
import useShelfMotion from './useShelfMotion';
import {isAlert, rank} from './actions';
import {assessmentFacts, searchText, fullTime, areaHref, productLabel, shelfLabel, statusClass, statusLabel, taskDescription} from './presentation';

export default function TaskList({areas: sourceAreas, storeView, location, navigate, onOpen}) {
  const query = location.q || '';
  const filter = location.filter === 'attention' ? 'attention' : 'all';
  const areas = useMemo(() => [...sourceAreas].sort((a, b) => rank(a) - rank(b)), [sourceAreas]);
  const attention = areas.filter(area => isAlert(area));
  const shown = areas.filter(area => (filter === 'all' || isAlert(area)) &&
    searchText(`${area.product_name} ${area.area_id} ${shelfLabel(area)}`).includes(searchText(query)));
  const motionScope = useRef(null);
  useShelfMotion(motionScope, `${location.snapshot}:${location.q || ''}:${filter}:${sourceAreas.length}`);
  const follow = (event, area) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    onOpen(area);
  };
  return <section ref={motionScope} className="shelf-list" aria-labelledby="shelves-title">
    <div className="list-heading"><div><h2 id="shelves-title">Explore shelves</h2><p>Recorded images · Expected products from the planogram</p></div><span className="count">{areas.length} shelves</span></div>
    <div className="list-tools">
      <div className="filters" role="group" aria-label="Filter shelves">
        <button aria-pressed={filter === 'all'} onClick={() => navigate({filter: null}, true)}>All shelves <span>{areas.length}</span></button>
        <button aria-pressed={filter === 'attention'} onClick={() => navigate({filter: 'attention'}, true)}>With alerts <span>{attention.length}</span></button>
      </div>
      <label className="search-label"><span className="search-caption">Find a product or shelf</span><input name="shelf-search" type="search" autoComplete="off" placeholder="Find a product or shelf…" value={query} onChange={e => navigate({q: e.target.value || null}, true)}/></label>
    </div>
    <p className="sr-only" role="status">{shown.length} matching shelves.</p>
    {shown.length ? <ul className="task-list">{shown.map(area => <li key={area.area_id}>
      <a className={`shelf-task ${location.area === area.area_id ? 'selected' : ''}`} href={areaHref({...location, snapshot: area.snapshot_id}, area.area_id)}
        data-stock={assessmentFacts(area).length ? area.stock_level : undefined}
        aria-current={location.area === area.area_id ? 'true' : undefined} onClick={event => follow(event, area)}>
        <div className="task-media"><Evidence className="task-thumbnail" url={area.crop_url} alt="" thumbnail/><span className="photo-location">{shelfLabel(area)}</span><span className="photo-open" aria-hidden="true">↗</span></div>
        <div className="task-copy"><span className="shelf-location">{storeView ? `Camera ${area.camera_id}` : shelfLabel(area)}</span><span className="expected-label">Expected product</span><h3 title={area.product_name}>{productLabel(area.product_name)}</h3><p className="task-assessment">{taskDescription(area)}</p><div className="card-assessment"><span className={`status ${statusClass(area)}`}>{statusLabel(area)}</span><span className="card-time">{fullTime(area.captured_at)}</span></div><AssessmentBadges area={area}/><span className="card-cta">View shelf <span aria-hidden="true">↗</span></span></div>
        <span className="task-arrow" aria-hidden="true">→</span>
      </a>
    </li>)}</ul> : <div className="empty-state"><h3>{query ? 'No matching shelves' : 'No assessed alerts to show'}</h3><p>{query ? 'Try a different product name or shelf number.' : areas.some(area => area.fallback_used || area.prediction_source === 'mock') ? 'Some shelves have no reliable assessment. Browse their images before drawing conclusions.' : 'No stock or product issues were flagged in this observation.'}</p><button className="button secondary" onClick={() => navigate({q: null, filter: null}, true)}>Show all shelves</button></div>}
  </section>;
}
