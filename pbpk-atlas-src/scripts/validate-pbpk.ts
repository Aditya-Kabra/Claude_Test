// Numerical checks for the PBPK engine: run with `npm run test:pbpk`.
import assert from 'node:assert/strict';
import {simulate,derive,exposure,type Dosing} from '../app/pbpk/model.ts';
import {physiology} from '../app/pbpk/physiology.ts';
import {PRESETS} from '../app/pbpk/drugs.ts';

const close=(a:number,b:number,rel:number,msg:string)=>assert.ok(Math.abs(a-b)<=rel*Math.abs(b),`${msg}: ${a} vs ${b}`);

// Circulation closes: flow into venous blood equals cardiac output.
const phys=physiology();
close(phys.flow.rest+['brain','heart','muscle','adipose','skin','bone','kidney','testes'].reduce((s,id)=>s+phys.flow[id as never],0)+phys.hepaticFlow,phys.cardiacOutput,1e-12,'flow balance');
assert.ok(phys.flow.rest>0,'rest-of-body flow is positive');

for(const p of PRESETS){
 for(const route of ['iv-bolus','iv-infusion','oral'] as const){
  const dosing:Dosing={...p.dosing,route,weight:73};
  const sim=simulate(p.drug,dosing);
  // Mass balance: everything dosed is still in the body, eliminated, or unabsorbed.
  close(sim.remaining+sim.metabolized+sim.urine+sim.feces,sim.dosed,1e-6,`${p.drug.name} ${route} mass balance`);
  for(const series of Object.values(sim.conc))assert.ok(series.every(Number.isFinite),`${p.drug.name} ${route} finite`);
 }
 // IV bolus AUC matches dose / CL (plasma) once the profile has fully decayed.
 const d=derive(p.drug,phys),cl=d.hepaticClearance+d.renalClearance;
 const long=simulate(p.drug,{...p.dosing,route:'iv-bolus',doses:1,dose:10,weight:73,duration:Math.min(5000,15*d.vss/cl)},4000);
 const e=exposure(long.times,long.plasma,0);
 close(long.aucPlasma,10/cl,.03,`${p.drug.name} AUC = dose/CL`);
 // Terminal half-life consistent with Vss/CL within the usual spread for multi-compartment kinetics.
 assert.ok(e.halfLife&&e.halfLife>.3*Math.LN2*d.vss/cl&&e.halfLife<5*Math.LN2*d.vss/cl,`${p.drug.name} half-life ${e.halfLife}`);
 // Oral AUC scales with F.
 const oral=simulate(p.drug,{...p.dosing,route:'oral',doses:1,dose:10,weight:73,duration:Math.min(5000,15*d.vss/cl)},4000);
 const eo=exposure(oral.times,oral.plasma,0);
 close(oral.aucPlasma/long.aucPlasma,d.oralBioavailability,.05,`${p.drug.name} oral F`);
 console.log(`${p.drug.name.padEnd(10)} Vss ${(d.vss/73).toFixed(2)} L/kg  CL ${cl.toFixed(2)} L/h  t½ ${e.halfLife?.toFixed(1)} h  F ${d.oralBioavailability.toFixed(2)}`);
}
console.log('PBPK checks passed');
