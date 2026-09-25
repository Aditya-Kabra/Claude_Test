import {useEffect,useMemo,useRef,useState} from 'react';
import {fromAxis,toAxis,type TimeAxis} from './timeline.ts';

export interface Series {label:string;color:string;values:Float64Array}
interface Props {times:Float64Array;series:Series[];time:number;log:boolean;axis:TimeAxis;onSeek:(t:number)=>void}

const M={top:10,right:14,bottom:24,left:46};
export const fmt=(v:number)=>!Number.isFinite(v)?'–':v===0?'0':Math.abs(v)>=1000||Math.abs(v)<.001?v.toExponential(1):(p=>p.includes('.')?p.replace(/\.?0+$/,''):p)(v.toPrecision(3));

function niceTicks(max:number,count=4){const step=10**Math.floor(Math.log10(max/count)),err=max/count/step,s=step*(err>=7.5?10:err>=3.5?5:err>=1.5?2:1);const out=[];for(let v=0;v<=max+1e-9;v+=s)out.push(+v.toPrecision(6));return out;}

/** Concentration–time line chart with a draggable time cursor and a hover crosshair. */
const LOG_TICKS=[0,.05,.1,.25,.5,1,2,4,8,12,24,48,96,168,336,720];
export default function Chart({times,series,time,log,axis,onSeek}:Props){
 const host=useRef<HTMLDivElement>(null),[size,setSize]=useState({w:600,h:180}),[hover,setHover]=useState<number|null>(null),drag=useRef(false);
 useEffect(()=>{const el=host.current!;const ro=new ResizeObserver(()=>setSize({w:el.clientWidth,h:el.clientHeight}));ro.observe(el);return()=>ro.disconnect();},[]);
 const w=Math.max(200,size.w),h=Math.max(100,size.h),iw=w-M.left-M.right,ih=h-M.top-M.bottom,tMax=times[times.length-1]||1;
 const {y,yTicks,paths}=useMemo(()=>{
  let max=0;for(const s of series)for(const v of s.values)if(v>max)max=v;max=max||1;
  let y:(v:number)=>number,yTicks:number[];
  if(log){const hi=Math.ceil(Math.log10(max)),lo=hi-4;y=v=>M.top+ih*(1-(Math.log10(Math.max(v,10**lo))-lo)/(hi-lo));yTicks=Array.from({length:hi-lo+1},(_,i)=>10**(lo+i));}
  else{yTicks=niceTicks(max);const top=yTicks[yTicks.length-1];y=v=>M.top+ih*(1-v/top);}
  const x=(t:number)=>M.left+iw*toAxis(t,tMax,axis);
  const paths=series.map(s=>{let d='';for(let i=0;i<times.length;i++)d+=(i?'L':'M')+x(times[i]).toFixed(1)+','+y(s.values[i]).toFixed(1);return d;});
  return {y,yTicks,paths};
 },[series,times,log,axis,iw,ih,tMax]);
 const x=(t:number)=>M.left+iw*toAxis(t,tMax,axis);
 let xTicks=axis==='linear'?niceTicks(tMax,Math.max(2,Math.floor(iw/80))).filter(t=>t<=tMax):[];
 if(axis==='log'){let last=-Infinity;for(const t of [...LOG_TICKS.filter(t=>t<tMax),tMax]){if(x(t)-last>=34){xTicks.push(t);last=x(t);}}if(xTicks[xTicks.length-1]!==tMax&&xTicks.length>1){xTicks[xTicks.length-1]=tMax;}}
 const toTime=(e:React.PointerEvent)=>{const r=host.current!.getBoundingClientRect();return fromAxis(Math.min(1,Math.max(0,(e.clientX-r.left-M.left)/iw)),tMax,axis);};
 let hi:number|null=null;if(hover!==null){hi=0;for(let i=1;i<times.length;i++)if(Math.abs(times[i]-hover)<Math.abs(times[hi]-hover))hi=i;}
 return <div className="pk-chart" ref={host}
  onPointerDown={e=>{drag.current=true;(e.target as Element).setPointerCapture?.(e.pointerId);onSeek(toTime(e));}}
  onPointerMove={e=>{const t=toTime(e);setHover(t);if(drag.current)onSeek(t);}}
  onPointerUp={()=>{drag.current=false;}} onPointerLeave={()=>{if(!drag.current)setHover(null);}}>
  <svg width={w} height={h} role="img" aria-label={`Concentration over time: ${series.map(s=>s.label).join(', ')}`}>
   {yTicks.map(v=><g key={v}><line x1={M.left} x2={w-M.right} y1={y(v)} y2={y(v)} className="pk-gridline"/><text x={M.left-6} y={y(v)} className="pk-tick" textAnchor="end" dominantBaseline="middle">{fmt(v)}</text></g>)}
   {xTicks.map(t=><text key={t} x={x(t)} y={h-6} className="pk-tick" textAnchor="middle">{fmt(t)}{t===xTicks[xTicks.length-1]?' h':''}</text>)}
   {paths.map((d,i)=><path key={series[i].label} d={d} fill="none" stroke={series[i].color} strokeWidth={2} strokeLinejoin="round"/>)}
   <line x1={x(time)} x2={x(time)} y1={M.top} y2={M.top+ih} className="pk-cursor"/>
   {hi!==null&&<><line x1={x(times[hi])} x2={x(times[hi])} y1={M.top} y2={M.top+ih} className="pk-crosshair"/>{series.map(s=><circle key={s.label} cx={x(times[hi])} cy={y(s.values[hi])} r={4} fill={s.color} stroke="#fff" strokeWidth={2}/>)}</>}
  </svg>
  {hi!==null&&<div className="pk-tooltip" style={{left:Math.min(x(times[hi])+12,w-170),top:M.top}}><strong>{fmt(times[hi])} h</strong>{series.map(s=><span key={s.label}><i style={{background:s.color}}/>{s.label}<b>{fmt(s.values[hi])} mg/L</b></span>)}</div>}
 </div>;
}
