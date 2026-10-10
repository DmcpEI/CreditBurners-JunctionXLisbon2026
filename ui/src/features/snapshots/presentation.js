import {action} from './actions.js';

export const dateLabel = value => new Intl.DateTimeFormat(undefined, {dateStyle: 'medium'}).format(new Date(value));
export const timeLabel = value => new Intl.DateTimeFormat(undefined, {hour: '2-digit', minute: '2-digit', timeZoneName: 'short'}).format(new Date(value));
export const fullTime = value => `${dateLabel(value)} · ${timeLabel(value)}`;
export const productLabel = value => {
  const name = value || 'Unnamed product';
  const withoutRetailMetadata = name.replace(/\s+\b(?:CNT|CAT|CAL)\b.*$/i, '').replace(/\s+\b(?:KG|UNI|IMP)\b.*$/i, '').trim();
  return (withoutRetailMetadata || name).toLocaleLowerCase().replace(/(^|\s)\S/g, letter => letter.toLocaleUpperCase());
};
export const shelfLabel = area => `Shelf ${area.area_id.split('_').at(-1)}`;
export const statusLabel = area => area.fallback_used ? 'Not assessed' : action(area) === 'Inspect' ? 'Needs inspection' : action(area) === 'OK' ? 'No action needed' : action(area);
export const statusClass = area => ({Inspect: 'inspect', Restock: 'restock', 'Check product': 'mismatch', 'Check stock': 'low', OK: 'okay'})[action(area)];
export const taskDescription = area => {
  if (area.fallback_used) return 'Image available. Stock and product match are not assessed.';
  if (area.visibility !== 'clear') return 'Stock cannot be confirmed from this image.';
  if (area.stock_level === 'empty') return 'Shelf appears empty. Check for a restock.';
  if (!area.planogram_compliant) return 'Check the produce against the expected product.';
  if (area.stock_level === 'half') return 'Stock appears partly depleted. Check the shelf.';
  return 'No stock or product issue flagged.';
};
export function areaHref(location, id) {
  const params = new URLSearchParams(location);
  params.set('area', id);
  return `?${params}`;
}

export const searchText = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();
export function assessmentFacts(area) {
  if (area.fallback_used || area.visibility !== 'clear' || area.prediction_source === 'mock') return [];
  return [
    {label: {empty:'Empty', half:'Half stocked', full:'Full'}[area.stock_level], tone: {empty:'restock',half:'low',full:'okay'}[area.stock_level]},
    {label: area.planogram_compliant ? 'Expected product matches' : 'Product mismatch', tone: area.planogram_compliant ? 'okay' : 'mismatch'}
  ];
}
