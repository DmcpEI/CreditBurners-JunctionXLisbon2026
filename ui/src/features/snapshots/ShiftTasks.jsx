import React, {useState} from 'react';
import Evidence from './Evidence';
import {action, rank} from './actions';
import {timeLabel, productLabel, shelfLabel, statusClass, statusLabel, taskDescription} from './presentation';

// Simulated live view: tasks from the latest image of each camera only (the brief's staff scenario).
export default function ShiftTasks({areas, cameras, onOpen}) {
  const [expanded, setExpanded] = useState(false);
  const urgent = areas.filter(area => action(area) === 'Restock').length;
  const restock = areas.filter(area => action(area) === 'Check stock').length;
  const ordered = [...areas].sort((a, b) => rank(a) - rank(b) || a.camera_id.localeCompare(b.camera_id));
  const shown = expanded ? ordered : ordered.slice(0, 5);
  return <section className="shift-tasks overview-content" aria-labelledby="shift-title">
    <div className="shift-heading">
      <p className="shift-live"><i aria-hidden="true"/>Live · latest image from each of {cameras} cameras</p>
      <h2 id="shift-title">{areas.length ? 'What needs doing first' : 'No shelf tasks right now'}</h2>
      <div className="shift-counts" role="list">
        <span role="listitem" className="shift-count urgent"><strong>{urgent}</strong> restock urgently</span>
        <span role="listitem" className="shift-count low"><strong>{restock}</strong> restock soon</span>
      </div>
    </div>
    {shown.length > 0 && <ul className="alerts-list shift-list">{shown.map(area => <li key={`${area.snapshot_id}:${area.area_id}`}>
      <button className={`alert-card ${statusClass(area)}`} data-stock={area.stock_level} onClick={() => onOpen(area)}>
        <div className="alert-card-top"><Evidence className="alert-thumbnail" url={area.crop_url} alt="" thumbnail/><div>
          <span className="alert-action">{statusLabel(area)}</span>
          <strong>{productLabel(area.product_name)}</strong>
          <span>{shelfLabel(area)} · Camera {area.camera_id} · seen {timeLabel(area.captured_at)}</span>
        </div></div>
        <p>{taskDescription(area)}</p>
      </button></li>)}</ul>}
    {ordered.length > 5 && <button className="button secondary shift-more" aria-expanded={expanded} onClick={() => setExpanded(value => !value)}>{expanded ? 'Show fewer' : `Show all ${ordered.length} tasks`}</button>}
  </section>;
}
