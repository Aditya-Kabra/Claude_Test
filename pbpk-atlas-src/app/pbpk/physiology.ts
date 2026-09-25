// Reference adult male physiology for a whole-body, perfusion-limited PBPK model.
// Volumes and blood-flow fractions follow ICRP Publication 89 reference male values
// (73 kg) as commonly tabulated for PBPK (e.g. Brown et al. 1997; Jones & Rowland-Yeo 2013).
// Tissue composition (fractions of tissue volume) follows the human values tabulated by
// Poulin & Theil (J Pharm Sci 2000/2002). Pancreas, testes and "rest" have no entry there;
// they borrow gut, kidney and muscle composition respectively and are marked as assumed.

export type CompartmentId =
 |'venous'|'lung'|'arterial'
 |'brain'|'heart'|'muscle'|'adipose'|'skin'|'bone'|'kidney'|'testes'|'rest'
 |'gut'|'spleen'|'pancreas'|'liver';

export interface Composition {neutralLipid:number;phospholipid:number;water:number;assumed?:string}

export interface CompartmentInfo {
 id:CompartmentId;name:string;
 /** Volume in L for the 73 kg reference male. */
 volume:number;
 /** Fraction of cardiac output perfusing the tissue (liver: hepatic-artery share only). */
 flowFraction:number;
 composition?:Composition;
 blood?:boolean;
 note?:string;
}

export const REFERENCE_WEIGHT=73;
/** Cardiac output, L/h (6.5 L/min). */
export const REFERENCE_CARDIAC_OUTPUT=390;
/** Glomerular filtration rate, L/h (125 mL/min). */
export const REFERENCE_GFR=7.5;

const gut:Composition={neutralLipid:.0487,phospholipid:.0163,water:.718};
const kidney:Composition={neutralLipid:.0207,phospholipid:.0162,water:.783};
const muscle:Composition={neutralLipid:.0238,phospholipid:.0072,water:.76};
export const PLASMA:Composition={neutralLipid:.0035,phospholipid:.00225,water:.945};

export const COMPARTMENTS:CompartmentInfo[]=[
 {id:'venous',name:'Venous blood',volume:5.3*2/3,flowFraction:0,blood:true},
 {id:'arterial',name:'Arterial blood',volume:5.3/3,flowFraction:0,blood:true},
 {id:'lung',name:'Lung',volume:.5,flowFraction:1,composition:{neutralLipid:.003,phospholipid:.009,water:.811},note:'Receives the whole cardiac output.'},
 {id:'brain',name:'Brain',volume:1.45,flowFraction:.12,composition:{neutralLipid:.051,phospholipid:.0565,water:.77}},
 {id:'heart',name:'Heart',volume:.33,flowFraction:.04,composition:{neutralLipid:.0115,phospholipid:.0166,water:.758}},
 {id:'liver',name:'Liver',volume:1.8,flowFraction:.065,composition:{neutralLipid:.0348,phospholipid:.0252,water:.751},note:'Hepatic artery 6.5% of cardiac output plus portal inflow from gut, spleen and pancreas. Site of metabolic clearance.'},
 {id:'gut',name:'Gut',volume:1.65,flowFraction:.15,composition:gut,note:'Drains to the liver through the portal vein. Oral doses are absorbed here.'},
 {id:'spleen',name:'Spleen',volume:.15,flowFraction:.03,composition:{neutralLipid:.0201,phospholipid:.0198,water:.788},note:'Drains to the liver through the portal vein.'},
 {id:'pancreas',name:'Pancreas',volume:.14,flowFraction:.01,composition:{...gut,assumed:'gut'},note:'Drains to the liver through the portal vein.'},
 {id:'kidney',name:'Kidney',volume:.31,flowFraction:.19,composition:kidney,note:'Site of renal clearance.'},
 {id:'muscle',name:'Muscle',volume:29,flowFraction:.17,composition:muscle},
 {id:'adipose',name:'Adipose',volume:18.2,flowFraction:.05,composition:{neutralLipid:.79,phospholipid:.002,water:.18},note:'BodyParts3D has no adipose geometry, so this compartment appears only in the list and chart.'},
 {id:'skin',name:'Skin',volume:3.3,flowFraction:.05,composition:{neutralLipid:.0284,phospholipid:.0111,water:.718}},
 {id:'bone',name:'Bone',volume:10.5,flowFraction:.05,composition:{neutralLipid:.074,phospholipid:.0011,water:.439}},
 {id:'testes',name:'Testes',volume:.035,flowFraction:.0005,composition:{...kidney,assumed:'kidney'}},
 {id:'rest',name:'Rest of body',volume:2.5,flowFraction:0,composition:{...muscle,assumed:'muscle'},note:'All other tissues. Its flow closes the circulation balance.'},
];

export const COMPARTMENT=Object.fromEntries(COMPARTMENTS.map(c=>[c.id,c])) as Record<CompartmentId,CompartmentInfo>;

/** Tissues drained directly into venous blood (liver collects the portal organs). */
export const SYSTEMIC:CompartmentId[]=['brain','heart','muscle','adipose','skin','bone','kidney','testes','rest','liver'];
export const PORTAL:CompartmentId[]=['gut','spleen','pancreas'];
export const TISSUES:CompartmentId[]=['lung',...SYSTEMIC,...PORTAL];

export interface Physiology {weight:number;cardiacOutput:number;gfr:number;volume:Record<CompartmentId,number>;flow:Record<CompartmentId,number>;hepaticFlow:number}

/** Scale the reference male: volumes with body weight, flows allometrically (weight^0.75). */
export function physiology(weight=REFERENCE_WEIGHT):Physiology{
 const vs=weight/REFERENCE_WEIGHT,fs=vs**.75,co=REFERENCE_CARDIAC_OUTPUT*fs;
 const volume={} as Record<CompartmentId,number>,flow={} as Record<CompartmentId,number>;
 for(const c of COMPARTMENTS){volume[c.id]=c.volume*vs;flow[c.id]=c.flowFraction*co;}
 flow.lung=co;flow.venous=flow.arterial=co;
 const named=SYSTEMIC.filter(id=>id!=='rest').reduce((s,id)=>s+flow[id],0)+PORTAL.reduce((s,id)=>s+flow[id],0);
 flow.rest=co-named;
 const hepaticFlow=flow.liver+PORTAL.reduce((s,id)=>s+flow[id],0);
 return {weight,cardiacOutput:co,gfr:REFERENCE_GFR*fs,volume,flow,hepaticFlow};
}
