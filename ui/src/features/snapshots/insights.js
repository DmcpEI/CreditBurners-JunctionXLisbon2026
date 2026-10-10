// Shelf study maths: saved stock assessments over the recorded day, for the store, a camera or a product.
// Stock levels are model estimates on hourly images, so single changes are noisy: a change counts unless the next
// image goes straight back (A-B-A flicker). Nothing here measures sales.
export const LEVEL = {empty: 0, half: 1, full: 2};

const usable = (snapshot, area, includePreview) => !area.fallback_used && area.visibility === 'clear' && area.stock_level in LEVEL &&
  (area.manual_preview ? includePreview : snapshot.prediction_source !== 'mock');

export function observations(snapshots, {category = name => name, includePreview = false} = {}) {
  return snapshots.flatMap(snapshot => snapshot.areas.filter(area => usable(snapshot, area, includePreview)).map(area => ({
    t: Date.parse(snapshot.captured_at), hour: new Date(snapshot.captured_at).getHours(), snapshot_id: snapshot.snapshot_id,
    camera_id: snapshot.camera_id, area_id: area.area_id, product_name: area.product_name, category: category(area.product_name),
    level: LEVEL[area.stock_level]})));
}

const count = list => ({n: list.length, empty: list.filter(o => o.level === 0).length, half: list.filter(o => o.level === 1).length,
  full: list.filter(o => o.level === 2).length});
const low = c => c.n ? (c.empty + c.half) / c.n : 0;

export function byHour(obs) {
  const hours = new Map();
  for (const o of obs) hours.set(o.hour, [...(hours.get(o.hour) || []), o]);
  return [...hours].sort((a, b) => a[0] - b[0]).map(([hour, list]) => ({hour, ...count(list)}));
}

// Groups ranked by share of observations that were empty or half; `latest_low` points at evidence to open.
export function rank(obs, key, label = o => o[key]) {
  const groups = new Map();
  for (const o of obs) groups.set(o[key], [...(groups.get(o[key]) || []), o]);
  return [...groups.values()].map(list => {
    const lows = list.filter(o => o.level < 2).sort((a, b) => b.t - a.t);
    return {key: list[0][key], label: label(list[0]), first: list[0], ...count(list), low: low(count(list)), latest_low: lows[0] || null};
  }).sort((a, b) => b.low - a.low || b.empty - a.empty || String(a.key).localeCompare(String(b.key)));
}

// Per shelf: confirmed level changes and empty spells (start, refill time). Spells starting at a shelf's first image
// of the day are the overnight state, not a sales event, and are left out.
export function shelfEvents(obs) {
  const shelves = new Map();
  for (const o of obs) shelves.set(`${o.camera_id}:${o.area_id}`, [...(shelves.get(`${o.camera_id}:${o.area_id}`) || []), o]);
  const changes = [], spells = [];
  for (const list of shelves.values()) {
    const seq = list.sort((a, b) => a.t - b.t);
    const steps = [seq[0]];
    for (let i = 1; i < seq.length - 1; i++) if (seq[i].level !== steps.at(-1).level && seq[i + 1].level !== steps.at(-1).level) steps.push(seq[i]);
    for (let i = 1; i < steps.length; i++) changes.push({...steps[i], from: steps[i - 1].level});
    steps.forEach((step, i) => {
      if (step.level !== 0 || step === seq[0]) return;
      const refill = steps[i + 1];
      spells.push({...step, minutes: refill ? (refill.t - step.t) / 60000 : null, open_until: refill ? null : seq.at(-1).t});
    });
  }
  return {changes, spells};
}

export function median(values) {
  const v = [...values].sort((a, b) => a - b);
  return v.length ? (v.length % 2 ? v[(v.length - 1) / 2] : (v[v.length / 2 - 1] + v[v.length / 2]) / 2) : null;
}

export function summary(obs) {
  const {changes, spells} = shelfEvents(obs);
  const refilled = spells.filter(s => s.minutes !== null);
  return {...count(obs), low: low(count(obs)), changes: changes.length, spells: spells.length, refilled: refilled.length,
    medianRefill: median(refilled.map(s => s.minutes)), stillEmpty: spells.length - refilled.length};
}
