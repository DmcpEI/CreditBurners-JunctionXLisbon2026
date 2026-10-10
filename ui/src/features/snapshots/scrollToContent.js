export function scrollToContent(element) {
  if (!element) return;
  const offset=['.app-header','.study-toolbar'].reduce((height,selector)=>{
    const control=document.querySelector(selector);
    return height+(control && ['sticky','fixed'].includes(getComputedStyle(control).position) ? control.getBoundingClientRect().height : 0);
  },12);
  window.scrollTo({top:Math.max(0,window.scrollY+element.getBoundingClientRect().top-offset),behavior:'instant'});
}
