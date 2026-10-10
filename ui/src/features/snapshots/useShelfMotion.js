import {useEffect} from 'react';

export default function useShelfMotion(scope, version) {
  useEffect(() => {
    const root = scope.current;
    if (!root || !window.IntersectionObserver) return;
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (preference.matches) return;
    const animations = new Set();
    const observer = new IntersectionObserver(entries => {
      entries.forEach((entry, index) => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        const animation = entry.target.animate([
          {opacity: 0, transform: 'translateY(24px) scale(.98)'},
          {opacity: 1, transform: 'translateY(0) scale(1)'}
        ], {duration: 550, delay: Math.min(index, 5) * 45, easing: 'cubic-bezier(.22,1,.36,1)', fill: 'backwards'});
        animations.add(animation);
        animation.finished.then(() => animations.delete(animation)).catch(() => {});
      });
    }, {threshold: .08});
    root.querySelectorAll('.task-list > li').forEach(element => observer.observe(element));
    const stop = () => {
      if (preference.matches) {
        observer.disconnect();
        animations.forEach(animation => animation.cancel());
      }
    };
    preference.addEventListener('change', stop);
    return () => {
      observer.disconnect();
      preference.removeEventListener('change', stop);
      animations.forEach(animation => animation.cancel());
    };
  }, [scope, version]);
}

export function transitionShelf(update) {
  if (!document.startViewTransition || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    update();
    return;
  }
  document.startViewTransition(update);
}
