// Log-like time warp: u in [0,1] maps to t in [0,T] with fine resolution early (where distribution
// happens within minutes) and coarse resolution late. TAU sets where the curve bends from linear to log.
const tau=(T:number)=>Math.max(T,1e-6)/400;
export const warp=(u:number,T:number)=>tau(T)*((1+T/tau(T))**Math.min(1,Math.max(0,u))-1);
export const unwarp=(t:number,T:number)=>Math.log(1+Math.max(0,t)/tau(T))/Math.log(1+T/tau(T));
export type TimeAxis='log'|'linear';
export const toAxis=(t:number,T:number,axis:TimeAxis)=>axis==='log'?unwarp(t,T):t/(T||1);
export const fromAxis=(u:number,T:number,axis:TimeAxis)=>axis==='log'?warp(u,T):u*T;
