import type {Dosing,Drug} from './model.ts';

// Illustrative compounds with approximate literature properties. CLint,u was back-calculated from
// typical human plasma clearance with the well-stirred liver model, and the Kp scalar matches the
// predicted Vss to typical reported values (Poulin–Theil over-predicts for bases and acids). Values are
// for exploration only.
export interface Preset {drug:Drug;dosing:Omit<Dosing,'weight'>;summary:string}

export const PRESETS:Preset[]=[
 {summary:'Lipophilic weak base with high hepatic (CYP3A) clearance.',
  drug:{kpScalar:.25,name:'Midazolam',logP:3.9,type:'base',pKa:6,fu:.03,bp:.66,clint:1350,clr:null,ka:3,fa:1},
  dosing:{route:'iv-bolus',dose:2,infusionHours:.5,interval:24,doses:1,duration:12}},
 {summary:'Neutral, weakly bound compound with low clearance and near-complete absorption.',
  drug:{kpScalar:1,name:'Caffeine',logP:-.07,type:'neutral',pKa:0,fu:.7,bp:1,clint:10.7,clr:.1,ka:3,fa:1},
  dosing:{route:'oral',dose:100,infusionHours:.5,interval:24,doses:1,duration:36}},
 {summary:'Highly bound, lipophilic compound with low clearance and a long half-life.',
  drug:{kpScalar:.5,name:'Diazepam',logP:2.82,type:'base',pKa:3.4,fu:.013,bp:.58,clint:130,clr:null,ka:2,fa:1},
  dosing:{route:'oral',dose:10,infusionHours:.5,interval:24,doses:1,duration:96}},
 {summary:'Acid, extensively bound to albumin, dosed daily until it accumulates.',
  drug:{kpScalar:.05,name:'Warfarin',logP:2.7,type:'acid',pKa:5,fu:.01,bp:.55,clint:20,clr:null,ka:1.5,fa:1},
  dosing:{route:'oral',dose:5,infusionHours:.5,interval:24,doses:7,duration:240}},
];
