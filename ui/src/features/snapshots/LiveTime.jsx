import React from 'react';
import {timeLabel} from './presentation';

// Simulated live view: the latest recorded image stands in for the camera's live feed.
export default function LiveTime({at}) {
  return <span className="live-time"><i aria-hidden="true"/>Live · last seen {timeLabel(at)}</span>;
}
