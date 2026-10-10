import {useCallback, useEffect, useMemo, useRef, useState} from 'react';

const readLocation = () => Object.fromEntries(new URLSearchParams(window.location.search));
const sortFrames = frames => [...frames].sort((a, b) => Date.parse(a.captured_at) - Date.parse(b.captured_at));

export default function useSnapshots() {
  const [location, setLocation] = useState(readLocation);
  const [summaries, setSummaries] = useState([]);
  const [snapshot, setSnapshot] = useState(null);
  const [listLoading, setListLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const [storeSnapshots, setStoreSnapshots] = useState([]);
  const [storeLoading, setStoreLoading] = useState(true);
  const [storeError, setStoreError] = useState('');
  const cache = useRef(new Map());
  const storeView = location.scope !== 'camera' && location.view !== 'replay';
  const loadSnapshot = useCallback(id => {
    if (!cache.current.has(id)) {
      const request = fetch(`/api/snapshots/${encodeURIComponent(id)}`).then(response => {
        if (!response.ok) throw new Error('This observation is unavailable. Choose another camera or try again.');
        return response.json();
      }).catch(error => { cache.current.delete(id); throw error; });
      cache.current.set(id, request);
    }
    return cache.current.get(id);
  }, []);
  const [playing, setPlaying] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => { setReducedMotion(media.matches); if (media.matches) setPlaying(false); };
    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
  }, []);

  const navigate = useCallback((changes, replace = false) => {
    const url = new URL(window.location.href);
    for (const [key, value] of Object.entries(changes)) {
      if (value === null || value === '') url.searchParams.delete(key);
      else url.searchParams.set(key, value);
    }
    window.history[replace ? 'replaceState' : 'pushState']({}, '', url);
    setLocation(readLocation());
  }, []);

  useEffect(() => {
    const onBack = () => { setLocation(readLocation()); setPlaying(false); };
    window.addEventListener('popstate', onBack);
    return () => window.removeEventListener('popstate', onBack);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setListLoading(true);
    setError('');
    fetch('/api/snapshots', {signal: controller.signal})
      .then(response => {
        if (!response.ok) throw new Error('Recorded observations could not be loaded. Check the connection and try again.');
        return response.json();
      })
      .then(data => {
        const sorted = sortFrames(data);
        setSummaries(sorted);
        if (!sorted.length) { setSnapshot(null); setStoreSnapshots([]); setStoreLoading(false); setLoading(false); }
        if (sorted.length && !new URLSearchParams(window.location.search).has('snapshot')) {
          navigate({snapshot: sorted.at(-1).snapshot_id}, true);
        }
        setListLoading(false);
      })
      .catch(e => {
        if (e.name !== 'AbortError') { setError(e.message); setListLoading(false); }
      });
    return () => controller.abort();
  }, [retry, navigate]);

  const current = summaries.find(s => s.snapshot_id === location.snapshot);
  const frames = useMemo(() => sortFrames(summaries.filter(s => s.camera_id === current?.camera_id)), [summaries, current?.camera_id]);
  const position = frames.findIndex(s => s.snapshot_id === location.snapshot);
  const mode = location.view === 'replay' ? 'replay' : 'shelves';

  useEffect(() => {
    if (!location.snapshot || !summaries.length) return;
    let cancelled = false;
    setLoading(true);
    setError('');
    loadSnapshot(location.snapshot)
      .then(data => { if (!cancelled) { setSnapshot(data); setLoading(false); } })
      .catch(e => { if (!cancelled) { setError(e.message); setLoading(false); setPlaying(false); } });
    return () => { cancelled = true; };
  }, [location.snapshot, summaries, retry, loadSnapshot]);

  useEffect(() => {
    if (!summaries.length || !storeView) return;
    let cancelled = false;
    const latest = new Map();
    for (const summary of sortFrames(summaries)) latest.set(summary.camera_id, summary);
    setStoreLoading(true);
    setStoreError('');
    Promise.all([...latest.values()].map(summary => loadSnapshot(summary.snapshot_id)))
      .then(data => { if (!cancelled) { setStoreSnapshots(data); setStoreLoading(false); } })
      .catch(e => { if (!cancelled) { setStoreError(`The store overview could not be loaded. ${e.message}`); setStoreLoading(false); } });
    return () => { cancelled = true; };
  }, [summaries, storeView, retry, loadSnapshot]);

  useEffect(() => {
    if (!playing || loading || !frames.length) return;
    if (position >= frames.length - 1) { setPlaying(false); return; }
    const timer = setTimeout(() => navigate({snapshot: frames[position + 1].snapshot_id, area: null}, true), 3500);
    return () => clearTimeout(timer);
  }, [playing, loading, frames, position, navigate]);

  const pauseReplay = () => setPlaying(false);
  const selectCamera = camera => {
    setPlaying(false);
    if (camera === 'all') { navigate({scope: null, view: null, area: null}); return; }
    const latest = sortFrames(summaries.filter(s => s.camera_id === camera)).at(-1);
    if (latest) navigate({snapshot: latest.snapshot_id, area: null, scope: 'camera'});
  };
  const selectFrame = id => { setPlaying(false); navigate({snapshot: id, area: null}); };
  const selectMode = view => { setPlaying(false); navigate({view: view === 'shelves' ? null : view, scope: view === 'shelves' ? null : 'camera', area: null}); };
  const toggleReplay = () => {
    if (reducedMotion) return;
    if (!playing && position === frames.length - 1 && frames.length) navigate({snapshot: frames[0].snapshot_id, area: null}, true);
    setPlaying(value => !value);
  };

  return {
    summaries, snapshot, storeSnapshots, storeView, current, frames, position, mode, location, loading: listLoading || (summaries.length > 0 && storeView ? storeLoading : loading) || Boolean(location.area && loading),
    error: storeView ? (storeError || error) : error, playing, reducedMotion, navigate, selectCamera, selectFrame, selectMode, toggleReplay, pauseReplay,
    retry: () => { cache.current.clear(); setRetry(value => value + 1); },
  };
}
