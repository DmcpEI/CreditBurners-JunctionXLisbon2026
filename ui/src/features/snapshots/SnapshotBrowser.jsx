import CameraPreview from './CameraPreview';
import TypedHeadline from './TypedHeadline';
import BrandSymbol from './BrandSymbol';
import React, {useEffect, useRef} from 'react';
import {manualPreview} from './manualPreview';
import {withAssessmentMetadata} from './assessmentMetadata';
import useSnapshots from './useSnapshots';
import ObservationToolbar from './ObservationToolbar';
import TaskList from './TaskList';
import ShelfStudy from './ShelfStudy';
import StudyCameraControls from './StudyCameraControls';
import StoreCameras from './StoreCameras';
import ShelfDetail from './ShelfDetail';
import Evidence from './Evidence';
import {timeLabel} from './presentation';
import {isAlert} from './actions';
import AlertsPanel from './AlertsPanel';
import {flushSync} from 'react-dom';
import {transitionShelf} from './useShelfMotion';
import {scrollToContent} from './scrollToContent';

export default function SnapshotBrowser() {
  const browser = useSnapshots();
  const {snapshot: originalSnapshot, storeSnapshots: originalStoreSnapshots, storeView, summaries, location, mode, navigate, loading, error, selectMode} = browser;
  const demo = mode === 'shelves' && location.demo === '1';
  const snapshot = withAssessmentMetadata(demo ? manualPreview(originalSnapshot) : originalSnapshot);
  const storeSnapshots = originalStoreSnapshots.map(s=>withAssessmentMetadata(demo ? manualPreview(s) : s));
  const area = snapshot?.areas.find(a => a.area_id === location.area);
  const displayedSnapshots = storeView ? storeSnapshots : (snapshot ? [snapshot] : []);
  const displayedAreas = displayedSnapshots.flatMap(s => s.areas.map(a => ({...a, snapshot_id: s.snapshot_id, camera_id: s.camera_id, captured_at: s.captured_at, prediction_source: s.prediction_source})));
  const fallback = displayedAreas.some(a => a.fallback_used);
  const allFallback = displayedAreas.length > 0 && displayedAreas.every(a => a.fallback_used);
  const alerts = displayedAreas.filter(isAlert);
  const attention = alerts.length;
  const unassessed = displayedAreas.filter(a => a.fallback_used).length;
  const lastShelf = useRef(null);
  const lastShelfSnapshot = useRef(null);
  const listScroll = useRef(0);
  const previousArea = useRef(location.area);
  const previousPage = useRef(mode);
  const previousCamera = useRef(browser.current?.camera_id);
  const previousScope = useRef(location.scope);
  const openShelf = item => {
    lastShelf.current = item.area_id;
    lastShelfSnapshot.current = item.snapshot_id;
    listScroll.current = window.scrollY;
    transitionShelf(() => flushSync(() => navigate({snapshot: item.snapshot_id, area: item.area_id,focus:item.focus || null})));
  };
  const closeShelf = () => {
    if (lastShelf.current === location.area && lastShelfSnapshot.current === location.snapshot) window.history.back();
    else navigate({area: null,focus:null}, true);
  };
  useEffect(() => {
    if (loading) return;
    if (previousPage.current !== mode) {
      window.scrollTo({top:0,behavior:'instant'});
    } else if (previousArea.current && !location.area) {
      const shelf = lastShelf.current || previousArea.current;
      const target = document.querySelector(`.shelf-task[href*="area=${CSS.escape(shelf)}"]`);
      target?.focus({preventScroll: true});
      window.scrollTo({top: listScroll.current, behavior: 'instant'});
    } else if (!location.area && mode==='shelves' && location.scope==='camera' && previousCamera.current && (previousCamera.current!==browser.current?.camera_id || previousScope.current!==location.scope)) {
      scrollToContent(document.querySelector('.shelf-list'));
    }
    previousArea.current = location.area;
    previousPage.current = mode;
    previousCamera.current = browser.current?.camera_id;
    previousScope.current = location.scope;
  }, [location.area, mode, loading, location.scope, browser.current?.camera_id]);
  return <div className={`app-shell ${area ? 'detail-open' : 'gallery-view'} ${mode==='study'?'study-page':''}`}>
    <a className="skip-link" href="#main-content">Skip to shelf checklist</a>
    <header className="app-header"><a className="brand" href="/" aria-label="Sensei home"><BrandSymbol/>sensei<span className="brand-divider" aria-hidden="true"/><span className="brand-description">Shelf assistant</span></a><nav className="app-nav" aria-label="Main pages"><button aria-current={mode==='shelves' ? 'page' : undefined} onClick={()=>selectMode('shelves')}>Store view</button><button aria-current={mode==='study' ? 'page' : undefined} onClick={()=>selectMode('study')}>Shelf study</button></nav><div className="header-tools"><span className="recorded-label">Recorded dataset</span>{mode==='shelves' && <AlertsPanel areas={alerts} unavailable={displayedAreas.filter(a => a.fallback_used || (a.prediction_source === 'mock' && !a.manual_preview)).length} busy={loading || !!error || !displayedAreas.length} onOpen={openShelf}/>}</div></header>
    <main id="main-content">
      {demo && <aside className="manual-preview-notice"><strong>Demo · Simulated alerts</strong><p>Manual statuses on real photos. Not model predictions.</p><button onClick={() => navigate({demo:'0'},true)}>Exit preview</button></aside>}
      <div className="overview-content">
        <div className={`page-heading ${mode==='study' ? 'study-page-heading' : ''}`}><div><p className="section-kicker">Sensei / Produce workspace</p><h1>{mode==='study' ? 'Shelf study.' : <TypedHeadline/>}</h1><p>{mode==='study' ? 'Explore recorded images and compare shelf observations over time.' : 'Latest recorded images. Find your product and review the evidence.'}</p></div>{mode==='shelves' && storeView && storeSnapshots.length>0 && <CameraPreview snapshots={storeSnapshots} onOpen={openShelf}/>} {snapshot && mode==='shelves' && !storeView && <figure className="store-preview">{storeView ? <div className="store-preview-mosaic">{storeSnapshots.slice(0,3).map(frame=><Evidence key={frame.camera_id} url={frame.image_url} alt={`Recorded camera ${frame.camera_id}`}/>)}</div> : <Evidence url={snapshot.image_url} alt={`Recorded store view from camera ${snapshot.camera_id}`}/>}<figcaption><span>{storeView ? `${storeSnapshots.length} cameras · Your store` : `Camera ${snapshot.camera_id}`}</span><span>{timeLabel(snapshot.captured_at)} · Recorded image</span></figcaption></figure>}</div>
            {fallback && <aside className="baseline-notice"><span className="notice-symbol" aria-hidden="true">i</span><div><strong>{allFallback ? 'Images ready · Assessments unavailable' : 'Some results use fallback values'}</strong><details className="baseline-help"><summary>About these results</summary><p>{allFallback ? 'These are real recorded images. The expected products come from the planogram. Model assessments are not available in this run; no stock or product-match alerts can be confirmed.' : 'Some observations use default values rather than model predictions. Check the evidence for those shelves before acting.'}</p></details></div></aside>}
        {displayedSnapshots.some(s => s.prediction_source === 'mock') && <aside className="baseline-notice"><strong>Illustrative mock — not model output.</strong></aside>}
        {displayedSnapshots.some(s => s.context_mode === 'retrospective') && <aside className="baseline-notice"><strong>Retrospective analysis</strong><p>Later frames were used as context. This is not live monitoring.</p></aside>}
      </div>
      {mode==='study' && <div className="study-toolbar"><StudyCameraControls browser={browser}/></div>}
      {mode==='study' && area && <div className="study-detail-controls"><ObservationToolbar browser={browser} hideCamera/></div>}
      {browser.notice && <p className="study-note" role="status">{browser.notice}</p>}
      {error && <section className="error-state" role="alert"><h2>Observation unavailable</h2><p>{error}</p><button className="button primary" onClick={browser.retry}>Try again</button>{summaries.length > 0 && <button className="button secondary" onClick={() => browser.selectFrame(summaries.at(-1).snapshot_id)}>Open latest recorded image</button>}</section>}
      {loading && <div className="loading-state" role="status"><span>Loading shelf observations…</span><div className="skeleton-row"/><div className="skeleton-row"/><div className="skeleton-row"/></div>}
      {!loading && !error && !summaries.length && <section className="empty-state"><h2>No recorded observations yet</h2><p>Published shelf images will appear here when they are available.</p><button className="button primary" onClick={browser.retry}>Check again</button></section>}
      {snapshot && !loading && !error && <>{mode==='study' && <ShelfStudy browser={browser} onOpen={openShelf}/>} {storeView && <StoreCameras snapshots={storeSnapshots} onOpen={openShelf}/>}<div className="observation-summary overview-content" aria-live="polite"><div className="overview-stat"><strong>{displayedAreas.length}</strong><span>Shelves</span></div><div className="overview-stat"><strong>{storeView ? storeSnapshots.length : 1}</strong><span>Cameras</span></div><div className="overview-stat"><strong>{unassessed}</strong><span>Without assessment</span></div><div className="overview-stat"><strong>{allFallback ? '—' : attention}</strong><span>{allFallback ? 'Awaiting assessment' : 'Need attention'}</span></div></div><div className="workspace"><TaskList areas={displayedAreas} storeView={storeView} location={location} navigate={navigate} onOpen={openShelf}/><ShelfDetail snapshot={snapshot} area={area} cameraFirst={location.focus==='camera'} onBack={closeShelf} onSelectArea={id => navigate({area: id,focus:null}, true)}/></div></>}
    </main><footer className="app-footer">Sensei · Team Credit Burners<span>Recorded evidence. Staff make the final call.</span></footer>
  </div>;
}
