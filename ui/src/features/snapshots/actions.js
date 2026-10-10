export function action(a){if(a.fallback_used || a.visibility !== 'clear') return 'Inspect'; if(a.stock_level==='empty')return 'Restock'; if(!a.planogram_compliant)return 'Check product'; if(a.stock_level==='half')return 'Check stock';return 'OK';}
export const rank = a => ({Inspect:0,Restock:1,'Check product':2,'Check stock':3,OK:4})[action(a)];

export const isAlert = area => !area.fallback_used && area.prediction_source !== 'mock' && action(area) !== 'OK';

export function matchesAlertType(area, type) {
  if (!isAlert(area)) return false;
  if (type === 'all') return true;
  if (type === 'Inspect') return area.visibility !== 'clear';
  if (area.visibility !== 'clear') return false;
  if (type === 'Restock') return area.stock_level === 'empty';
  if (type === 'Check product') return !area.planogram_compliant;
  if (type === 'Check stock') return area.stock_level === 'half';
  return false;
}
