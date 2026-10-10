import React from 'react';
import {createRoot} from 'react-dom/client';
import SnapshotBrowser from './features/snapshots/SnapshotBrowser';
import './style.css';

window.history.scrollRestoration='manual';
window.scrollTo({top:0,behavior:'instant'});
createRoot(document.getElementById('root')).render(<SnapshotBrowser/>);
