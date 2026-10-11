import {action} from './actions.js';

const timeZone = 'Europe/Lisbon';
export const dateLabel = value => new Intl.DateTimeFormat(undefined, {dateStyle: 'medium', timeZone}).format(new Date(value));
export const timeLabel = value => new Intl.DateTimeFormat(undefined, {hour: '2-digit', minute: '2-digit', timeZoneName: 'short', timeZone}).format(new Date(value));
export const storeHour = value => Number(new Intl.DateTimeFormat('en-GB', {hour: '2-digit', hourCycle: 'h23', timeZone}).format(new Date(value)));
export const fullTime = value => `${dateLabel(value)} · ${timeLabel(value)}`;
export const productLabel = value => {
  const name = value || 'Unnamed product';
  const withoutRetailMetadata = name.replace(/\s+\b(?:CNT|CAT|CAL)\b.*$/i, '').replace(/\s+\b(?:KG|UNI|IMP)\b.*$/i, '').trim();
  return (withoutRetailMetadata || name).toLocaleLowerCase().replace(/(^|\s)\S/g, letter => letter.toLocaleUpperCase());
};
export const shelfLabel = area => `Shelf ${area.area_id.split('_').at(-1)}`;
export const statusLabel = area => area.fallback_used ? 'Not assessed' : ({Inspect:'Needs inspection',Restock:'Restock urgently','Check stock':'Restock',OK:'No restock needed','Check product':'Check product'})[action(area)];
export const statusClass = area => ({Inspect: 'inspect', Restock: 'restock', 'Check product': 'mismatch', 'Check stock': 'low', OK: 'okay'})[action(area)];
export const taskDescription = area => {
  if (area.fallback_used) return 'Image available. Stock has not been assessed.';
  if (area.visibility !== 'clear') return 'Stock cannot be confirmed from this image.';
  if (area.stock_level === 'empty') return 'Shelf appears empty. Check for a restock.';
  if (!area.planogram_compliant) return 'Check the produce against the expected product.';
  if (area.stock_level === 'half') return 'Stock appears partly depleted. Check the shelf before replenishing.';
  return area.product_assessed === false ? 'No stock issue flagged.' : 'No stock or product issue flagged.';
};
export function areaHref(location, id) {
  const params = new URLSearchParams(location);
  params.set('area', id);
  return `?${params}`;
}

export const searchText = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();
export const matchesProduct = (area, query, englishName = '') =>
  searchText(`${area.product_name} ${englishName} ${area.area_id} ${shelfLabel(area)}`).includes(searchText(query));
export function assessmentFacts(area) {
  if (area.fallback_used || area.visibility !== 'clear' || (area.prediction_source === 'mock' && !area.manual_preview)) return [];
  return [
    {label: {empty:'Empty', half:'Half stocked', full:'Full'}[area.stock_level], tone: {empty:'restock',half:'low',full:'okay'}[area.stock_level]},
    {label: area.product_assessed === false ? 'Product not assessed' : area.planogram_compliant ? 'Expected product matches' : 'Product mismatch', tone: area.product_assessed === false ? 'inspect' : area.planogram_compliant ? 'okay' : 'mismatch'}
  ];
}
