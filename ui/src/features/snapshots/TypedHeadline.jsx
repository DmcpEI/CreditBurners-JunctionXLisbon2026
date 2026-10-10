import React, {useEffect,useState} from 'react';

const first='Fresh eyes.';
const second='Better shelves.';
export default function TypedHeadline() {
  const [count,setCount]=useState(()=>window.matchMedia('(prefers-reduced-motion: reduce)').matches ? first.length+second.length : 0);
  useEffect(()=>{
    const preference=window.matchMedia('(prefers-reduced-motion: reduce)');
    let timer;
    const stop=()=>{if(preference.matches){window.clearInterval(timer);setCount(first.length+second.length);}};
    if(!preference.matches) timer=window.setInterval(()=>setCount(value=>{if(value>=first.length+second.length){window.clearInterval(timer);return value;}return value+1;}),65);
    preference.addEventListener('change',stop);
    return ()=>{window.clearInterval(timer);preference.removeEventListener('change',stop);};
  },[]);
  const line=(text,visible)=> <span className="typed-line"><span className="typed-reserve" aria-hidden="true">{text}</span><span className="typed-ink" aria-hidden="true">{text.slice(0,visible)}</span></span>;
  return <span className="typed-headline"><span className="sr-only">{first} {second}</span>{line(first,Math.min(count,first.length))}<br/>{line(second,Math.max(0,count-first.length))}</span>;
}
