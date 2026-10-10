export function action(a){if(a.fallback_used || a.visibility !== 'clear') return 'Inspect'; if(a.stock_level==='empty')return 'Restock'; if(!a.planogram_compliant)return 'Check product'; if(a.stock_level==='half')return 'Check stock';return 'OK';}
export const rank = a => ({Inspect:0,Restock:1,'Check product':2,'Check stock':3,OK:4})[action(a)];

export const isAlert = area => !area.fallback_used && area.prediction_source !== 'mock' && action(area) !== 'OK';
