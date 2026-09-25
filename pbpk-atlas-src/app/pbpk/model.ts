// Whole-body, perfusion-limited PBPK model.
// Each tissue T is well stirred: V_T dC_T/dt = Q_T (C_in - C_T / Kb_T), with Kb_T = Kp_T / B:P
// the tissue:blood partition coefficient. Gut, spleen and pancreas drain into the liver.
// Hepatic clearance acts on unbound drug leaving the liver (CLint,u · fu · C_liver / Kp_liver), which
// reproduces the well-stirred liver model at steady state. Renal clearance acts on plasma leaving
// the kidney. Oral doses enter a gut lumen and are absorbed first-order into gut tissue.
import {warp} from './timeline.ts';
import {COMPARTMENTS,COMPARTMENT,PLASMA,PORTAL,SYSTEMIC,TISSUES,physiology,type CompartmentId,type Composition,type Physiology} from './physiology.ts';

export type CompoundType='neutral'|'acid'|'base';
export type Route='iv-bolus'|'iv-infusion'|'oral';

export interface Drug {
 name:string;
 /** Scales every tissue Kp, the usual way to match an observed Vss. */
 kpScalar:number;
 logP:number;type:CompoundType;pKa:number;
 /** Fraction unbound in plasma. */
 fu:number;
 /** Blood-to-plasma concentration ratio. */
 bp:number;
 /** Hepatic intrinsic clearance of unbound drug, L/h. */
 clint:number;
 /** Renal clearance from plasma, L/h. Null means filtration only (fu · GFR). */
 clr:number|null;
 /** First-order absorption rate constant, 1/h. */
 ka:number;
 /** Fraction of an oral dose absorbed from the lumen. */
 fa:number;
}

export interface Dosing {route:Route;dose:number;infusionHours:number;interval:number;doses:number;duration:number;weight:number}

export const STATE:CompartmentId[]=COMPARTMENTS.map(c=>c.id);
const index=Object.fromEntries(STATE.map((id,i)=>[id,i])) as Record<CompartmentId,number>;
const LUMEN=STATE.length,METABOLIZED=LUMEN+1,URINE=LUMEN+2,FECES=LUMEN+3,AUC=LUMEN+4,SIZE=LUMEN+5;

/** Poulin & Theil (2002) tissue:plasma partition coefficient. Adipose uses the vegetable oil:water
 * distribution coefficient (log Dvo = 1.115 log P - 1.35, ionised at pH 7.4) and no tissue binding. */
export function partition(drug:Drug,id:CompartmentId):number{
 const c:Composition|undefined=COMPARTMENT[id].composition;if(!c)return 1;
 const fu=drug.fu;
 if(id==='adipose'){
  const ionisation=drug.type==='acid'?1+10**(7.4-drug.pKa):drug.type==='base'?1+10**(drug.pKa-7.4):1;
  const d=10**(1.115*drug.logP-1.35)/ionisation;
  return (d*(c.neutralLipid+.3*c.phospholipid)+c.water+.7*c.phospholipid)/(d*(PLASMA.neutralLipid+.3*PLASMA.phospholipid)+PLASMA.water+.7*PLASMA.phospholipid)*fu;
 }
 const p=10**drug.logP,fut=1/(1+(1-fu)/fu*.5);
 return (p*(c.neutralLipid+.3*c.phospholipid)+c.water+.7*c.phospholipid)/(p*(PLASMA.neutralLipid+.3*PLASMA.phospholipid)+PLASMA.water+.7*PLASMA.phospholipid)*fu/fut;
}

export function renalClearance(drug:Drug,phys:Physiology){return drug.clr??drug.fu*phys.gfr;}

export interface Derived {
 kp:Record<CompartmentId,number>;
 /** Steady-state volume of distribution referenced to plasma, L. */
 vss:number;
 hepaticExtraction:number;
 /** Plasma clearances, L/h. */
 hepaticClearance:number;renalClearance:number;
 oralBioavailability:number;
}

export function derive(drug:Drug,phys:Physiology):Derived{
 const kp={} as Record<CompartmentId,number>;
 for(const id of STATE)kp[id]=COMPARTMENT[id].blood?drug.bp:partition(drug,id)*drug.kpScalar;
 const vss=(phys.volume.venous+phys.volume.arterial)*drug.bp+TISSUES.reduce((s,id)=>s+phys.volume[id]*kp[id],0);
 const fub=drug.fu/drug.bp,q=phys.hepaticFlow,e=fub*drug.clint/(q+fub*drug.clint);
 return {kp,vss,hepaticExtraction:e,hepaticClearance:q*e*drug.bp,renalClearance:renalClearance(drug,phys),oralBioavailability:drug.fa*(1-e)};
}

export interface Simulation {
 times:Float64Array;
 /** Concentration per compartment at each output time, mg/L (tissue or whole blood). */
 conc:Record<CompartmentId,Float64Array>;
 /** Venous plasma concentration, mg/L. */
 plasma:Float64Array;
 /** Amount (mg) eliminated or unabsorbed by the end. */
 metabolized:number;urine:number;feces:number;remaining:number;dosed:number;
 /** Exact plasma AUC over the simulation, mg·h/L (integrated with the model rather than from output points). */
 aucPlasma:number;
 derived:Derived;phys:Physiology;
 /** Largest concentration reached anywhere, mg/L, for colour scaling. */
 peak:number;
}

interface DoseEvent {time:number;amount:number;route:Route}

export function simulate(drug:Drug,dosing:Dosing,points=1200):Simulation{
 const phys=physiology(dosing.weight),derived=derive(drug,phys),{kp}=derived;
 const V=STATE.map(id=>phys.volume[id]),Q=STATE.map(id=>phys.flow[id]),Kb=STATE.map(id=>kp[id]/drug.bp);
 const co=phys.cardiacOutput,clr=derived.renalClearance,ka=drug.ka,fa=drug.fa;
 const iv=index.venous,ia=index.arterial,il=index.lung,ili=index.liver,ik=index.kidney;
 const systemic=SYSTEMIC.map(id=>index[id]),portal=PORTAL.map(id=>index[id]),perfused=[...SYSTEMIC,...PORTAL].map(id=>index[id]);
 const doses:DoseEvent[]=[];const count=Math.max(1,Math.round(dosing.doses));
 for(let d=0;d<count;d++){const time=d*dosing.interval;if(time<=dosing.duration)doses.push({time,amount:dosing.dose,route:dosing.route});}
 const infusions=dosing.route==='iv-infusion'?doses.map(d=>({start:d.time,end:d.time+Math.max(dosing.infusionHours,1e-3),rate:d.amount/Math.max(dosing.infusionHours,1e-3)})):[];
 const infusionRate=(t:number)=>{let r=0;for(const f of infusions)if(t>=f.start&&t<f.end)r+=f.rate;return r;};
 const derivative=(y:Float64Array,infusion:number,out:Float64Array)=>{
  const c=(i:number)=>y[i]/V[i];
  const cArt=c(ia),cLung=c(il);
  let venousIn=0;
  for(const i of systemic){const outflow=Q[i]*c(i)/Kb[i];venousIn+=i===ili?0:outflow;}
  for(const i of perfused)if(i!==ili)out[i]=Q[i]*(cArt-c(i)/Kb[i]);
  const liverOut=phys.hepaticFlow*c(ili)/Kb[ili];let portalIn=0;for(const i of portal)portalIn+=Q[i]*c(i)/Kb[i];
  const metabolism=drug.clint*drug.fu*c(ili)/kp.liver;
  out[ili]=Q[ili]*cArt+portalIn-liverOut-metabolism;
  const renal=clr*c(ik)/kp.kidney;out[ik]-=renal;
  const absorbed=ka*y[LUMEN];out[index.gut]+=fa*absorbed;
  out[iv]=venousIn+liverOut-co*c(iv)+infusion;
  out[il]=co*(c(iv)-cLung/Kb[il]);
  out[ia]=co*(cLung/Kb[il]-cArt);
  out[LUMEN]=-absorbed;out[METABOLIZED]=metabolism;out[URINE]=renal;out[FECES]=(1-fa)*absorbed;out[AUC]=c(iv)/drug.bp;
 };
 // Explicit RK4 with a step below the fastest compartment time constant.
 let fastest=co/V[iv]+co/V[ia]+co/(V[il]*Kb[il])+ka;
 for(const i of perfused)fastest=Math.max(fastest,Q[i]/(V[i]*Kb[i]));
 fastest=Math.max(fastest,phys.hepaticFlow/(V[ili]*Kb[ili])+drug.clint*drug.fu/(kp.liver*V[ili]),clr/(kp.kidney*V[ik])+Q[ik]/(V[ik]*Kb[ik]));
 // Output times are log-warped so the first minutes of distribution are resolved as well as the tail.
 const duration=Math.max(dosing.duration,.1),outTimes=Array.from({length:points},(_,n)=>n===points-1?duration:warp(n/(points-1),duration)),h=Math.min(duration/points,.9/fastest);
 const y=new Float64Array(SIZE),k1=new Float64Array(SIZE),k2=new Float64Array(SIZE),k3=new Float64Array(SIZE),k4=new Float64Array(SIZE),tmp=new Float64Array(SIZE);
 const times=new Float64Array(points),conc=Object.fromEntries(STATE.map(id=>[id,new Float64Array(points)])) as Record<CompartmentId,Float64Array>,plasma=new Float64Array(points);
 const breaks=[...new Set([...doses.map(d=>d.time),...infusions.map(f=>f.end)])].filter(t=>t>0&&t<duration).sort((a,b)=>a-b);
 let t=0,nextDose=0,nextOutput=0,peak=0;const dosed=doses.reduce((s,d)=>s+d.amount,0);
 const applyDoses=()=>{while(nextDose<doses.length&&doses[nextDose].time<=t+1e-9){const d=doses[nextDose++];if(d.route==='iv-bolus')y[iv]+=d.amount;else if(d.route==='oral')y[LUMEN]+=d.amount;}};
 const record=()=>{while(nextOutput<points&&outTimes[nextOutput]<=t+1e-9){const n=nextOutput++;times[n]=outTimes[n];for(let i=0;i<STATE.length;i++){const v=Math.max(0,y[i]/V[i]);conc[STATE[i]][n]=v;if(v>peak)peak=v;}plasma[n]=Math.max(0,y[iv]/V[iv]/drug.bp);}};
 const step=(dt:number)=>{
  // Infusions switch only at integration breaks, so the rate is constant across a step.
  const rate=infusionRate(t+dt/2);
  k1.fill(0);derivative(y,rate,k1);
  for(let i=0;i<SIZE;i++)tmp[i]=y[i]+dt/2*k1[i];k2.fill(0);derivative(tmp,rate,k2);
  for(let i=0;i<SIZE;i++)tmp[i]=y[i]+dt/2*k2[i];k3.fill(0);derivative(tmp,rate,k3);
  for(let i=0;i<SIZE;i++)tmp[i]=y[i]+dt*k3[i];k4.fill(0);derivative(tmp,rate,k4);
  for(let i=0;i<SIZE;i++)y[i]+=dt/6*(k1[i]+2*k2[i]+2*k3[i]+k4[i]);t+=dt;
 };
 applyDoses();record();
 while(t<duration-1e-9){
  const nextBreak=breaks.find(b=>b>t+1e-9)??duration,nextOut=outTimes[Math.min(nextOutput,points-1)],target=Math.min(nextBreak,nextOut,duration);
  const dt=Math.min(h,target-t);step(dt);
  if(Math.abs(t-target)<1e-9)t=target;
  applyDoses();record();
 }
 let remaining=y[LUMEN];for(let i=0;i<STATE.length;i++)remaining+=y[i];
 return {times,conc,plasma,metabolized:y[METABOLIZED],urine:y[URINE],feces:y[FECES],remaining,dosed,aucPlasma:y[AUC],derived,phys,peak};
}

export interface Exposure {cmax:number;tmax:number;auc:number;halfLife:number|null}

/** Non-compartmental summary of a concentration series. */
export function exposure(times:Float64Array,c:Float64Array,lastDose:number):Exposure{
 let cmax=0,tmax=0,auc=0;
 for(let i=0;i<c.length;i++){if(c[i]>cmax){cmax=c[i];tmax=times[i];}if(i)auc+=(c[i]+c[i-1])/2*(times[i]-times[i-1]);}
 // Terminal half-life from a log-linear fit to the final third of the post-dose, post-peak profile.
 const start=Math.max(times.findIndex(t=>t>=lastDose),0);let peakAfter=start;for(let i=start;i<c.length;i++)if(c[i]>c[peakAfter])peakAfter=i;
 const from=Math.max(peakAfter+1,Math.floor(c.length-(c.length-peakAfter)/3));
 let n=0,sx=0,sy=0,sxx=0,sxy=0;
 for(let i=from;i<c.length;i++)if(c[i]>0){const x=times[i],yv=Math.log(c[i]);n++;sx+=x;sy+=yv;sxx+=x*x;sxy+=x*yv;}
 const slope=n>=5?(n*sxy-sx*sy)/(n*sxx-sx*sx):NaN;
 return {cmax,tmax,auc,halfLife:slope<0?Math.LN2/-slope:null};
}
