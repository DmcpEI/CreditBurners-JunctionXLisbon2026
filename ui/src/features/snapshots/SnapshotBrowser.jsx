import React, {useEffect, useRef} from 'react';
import {manualPreview} from './manualPreview';
import useSnapshots from './useSnapshots';
import ObservationToolbar from './ObservationToolbar';
import TaskList from './TaskList';
import ShelfDetail from './ShelfDetail';
import Evidence from './Evidence';
import {timeLabel} from './presentation';
import {isAlert} from './actions';
import AlertsPanel from './AlertsPanel';
import {flushSync} from 'react-dom';
import {transitionShelf} from './useShelfMotion';

export default function SnapshotBrowser() {
  const browser = useSnapshots();
  const {snapshot: originalSnapshot, storeSnapshots: originalStoreSnapshots, storeView, summaries, location, mode, navigate, loading, error, selectMode} = browser;
  // Temporary demo default until Member1 results are integrated; demo=0 shows original records.
  const demo = location.demo !== '0';
  const snapshot = demo ? manualPreview(originalSnapshot) : originalSnapshot;
  const storeSnapshots = demo ? originalStoreSnapshots.map(manualPreview) : originalStoreSnapshots;
  const area = snapshot?.areas.find(a => a.area_id === location.area);
  const displayedSnapshots = storeView ? storeSnapshots : (snapshot ? [snapshot] : []);
  const displayedAreas = displayedSnapshots.flatMap(s => s.areas.map(a => ({...a, snapshot_id: s.snapshot_id, camera_id: s.camera_id, captured_at: s.captured_at, prediction_source: s.prediction_source})));
  const fallback = displayedAreas.some(a => a.fallback_used);
  const allFallback = displayedAreas.length > 0 && displayedAreas.every(a => a.fallback_used);
  const alerts = displayedAreas.filter(isAlert);
  const attention = alerts.length;
  const unassessed = displayedAreas.filter(a => a.fallback_used).length;
  const lastShelf = useRef(null);
  const listScroll = useRef(0);
  const previousArea = useRef(location.area);
  const openShelf = item => {
    lastShelf.current = item.area_id;
    listScroll.current = window.scrollY;
    transitionShelf(() => flushSync(() => navigate({snapshot: item.snapshot_id, area: item.area_id})));
  };
  const closeShelf = () => {
    if (lastShelf.current === location.area) window.history.back();
    else navigate({area: null}, true);
  };
  useEffect(() => {
    if (previousArea.current && !location.area) {
      const shelf = lastShelf.current || previousArea.current;
      const target = document.querySelector(`.shelf-task[href*="area=${CSS.escape(shelf)}"]`);
      target?.focus({preventScroll: true});
      if (window.matchMedia('(max-width: 760px)').matches) window.scrollTo({top: listScroll.current, behavior: 'instant'});
    }
    previousArea.current = location.area;
  }, [location.area]);
  return <div className={`app-shell ${area ? 'detail-open' : 'gallery-view'}`}>
    <a className="skip-link" href="#main-content">Skip to shelf checklist</a>
    <header className="app-header"><a className="brand" href="/" aria-label="Sensei home">sensei<span className="brand-divider" aria-hidden="true"/><span className="brand-description">Shelf assistant</span></a><div className="header-tools"><span className="recorded-label">Recorded dataset</span><AlertsPanel areas={alerts} unavailable={displayedAreas.filter(a => a.fallback_used || (a.prediction_source === 'mock' && !a.manual_preview)).length} busy={loading || !!error || !displayedAreas.length} onOpen={openShelf}/></div></header>
    <main id="main-content">
      {demo && <aside className="manual-preview-notice"><strong>Demo · Simulated alerts</strong><p>Manual statuses on real photos. Not model predictions.</p><button onClick={() => navigate({demo:'0'},true)}>Exit preview</button></aside>}
      <div className="overview-content">
        <div className="page-heading"><div><p className="section-kicker">Sensei / Produce workspace</p><h1>Fresh eyes.<br/><span>Better shelves.</span></h1><p>A closer look at every shelf. Find your product and review the evidence.</p></div>{snapshot && <figure className="store-preview"><Evidence url={snapshot.image_url} alt={`Recorded store view from camera ${snapshot.camera_id}`}/><figcaption><span>Camera {snapshot.camera_id}</span><span>{timeLabel(snapshot.captured_at)} · Recorded image</span></figcaption></figure>}<div className="view-switch" role="group" aria-label="Choose view"><button aria-pressed={mode === 'shelves'} onClick={() => selectMode('shelves')}>Shelves</button><button aria-pressed={mode === 'replay'} onClick={() => selectMode('replay')}>Timeline</button></div></div>
        <ObservationToolbar browser={browser}/>
        {mode === 'replay' && <p className="replay-explanation">Step through the recorded day. Hour-long gaps between images mean the exact time of a change is unknown.</p>}
        {fallback && <aside className="baseline-notice"><span className="notice-symbol" aria-hidden="true">i</span><div><strong>{allFallback ? 'Images ready · Assessments unavailable' : 'Some results use fallback values'}</strong><details className="baseline-help"><summary>About these results</summary><p>{allFallback ? 'These are real recorded images. The expected products come from the planogram. Model assessments are not available in this run; no stock or product-match alerts can be confirmed.' : 'Some observations use default values rather than model predictions. Check the evidence for those shelves before acting.'}</p></details></div></aside>}
        {displayedSnapshots.some(s => s.prediction_source === 'mock') && <aside className="baseline-notice"><strong>Illustrative mock — not model output.</strong></aside>}
        {displayedSnapshots.some(s => s.context_mode === 'retrospective') && <aside className="baseline-notice"><strong>Retrospective analysis</strong><p>Later frames were used as context. This is not live monitoring.</p></aside>}
      </div>
      {error && <section className="error-state" role="alert"><h2>Observation unavailable</h2><p>{error}</p><button className="button primary" onClick={browser.retry}>Try again</button>{summaries.length > 0 && <button className="button secondary" onClick={() => browser.selectFrame(summaries.at(-1).snapshot_id)}>Open latest recorded image</button>}</section>}
      {loading && <div className="loading-state" role="status"><span>Loading shelf observations…</span><div className="skeleton-row"/><div className="skeleton-row"/><div className="skeleton-row"/></div>}
      {!loading && !error && !summaries.length && <section className="empty-state"><h2>No recorded observations yet</h2><p>Published shelf images will appear here when they are available.</p><button className="button primary" onClick={browser.retry}>Check again</button></section>}
      {snapshot && !loading && !error && <><div className="observation-summary overview-content" aria-live="polite"><div className="overview-stat"><strong>{displayedAreas.length}</strong><span>Shelves</span></div><div className="overview-stat"><strong>{storeView ? storeSnapshots.length : 1}</strong><span>Cameras</span></div><div className="overview-stat"><strong>{unassessed}</strong><span>Without assessment</span></div><div className="overview-stat"><strong>{allFallback ? '—' : attention}</strong><span>{allFallback ? 'Awaiting assessment' : 'Need attention'}</span></div></div><div className="workspace"><TaskList areas={displayedAreas} storeView={storeView} location={location} navigate={navigate} onOpen={openShelf}/><ShelfDetail snapshot={snapshot} area={area} onBack={closeShelf} onSelectArea={id => navigate({area: id}, true)}/></div></>}
    </main><footer className="app-footer">Sensei · Team Credit Burners<span>Recorded evidence. Staff make the final call.</span></footer>
  </div>;
}
