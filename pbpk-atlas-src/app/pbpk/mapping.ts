import type {Part} from '../anatomy';
import type {CompartmentId} from './physiology';

// Assign each BodyParts3D mesh to the PBPK compartment it best represents. BodyParts3D models the
// liver and lungs mainly through their vessel, biliary and bronchial trees, so those trees stand in
// for the organs. Pulmonary arteries carry venous blood and pulmonary veins carry arterial blood.
const BRAIN_CAVITIES=/fourth ventricle|third ventricle|lateral ventricle|interventricular foramen|choroid plexus/i;
const GUT=/stomach|duoden|jejun|ile(um|ocecal)|colon|cecum|rectum|appendi|esophag|mesenter|mesocolon|taenia/i;

export function compartmentFor(p:Part):CompartmentId|null{
 const n=p.name;
 if(/hair|eyebrow/i.test(n))return null;
 if(/testis/i.test(n))return 'testes';
 if(/kidney/i.test(n))return 'kidney';
 if(/^spleen$/i.test(n))return 'spleen';
 if(/pancrea/i.test(n))return 'pancreas';
 if(/liver|hepat|portal vein/i.test(n))return 'liver';
 if(BRAIN_CAVITIES.test(n)||/pineal/i.test(n))return 'brain';
 if(/pulmonary (artery|trunk)|pulmonary trunk/i.test(n))return 'venous';
 if(/pulmonary vein/i.test(n))return 'arterial';
 switch(p.system){
  case 'digestive':return GUT.test(n)?'gut':'rest';
  case 'respiratory':return /bronch/i.test(n)?'lung':'rest';
  case 'cardiac':return 'heart';
  case 'nervous':return /nerve|ganglion|spinal/i.test(n)?'rest':'brain';
  case 'muscular':return 'muscle';
  case 'skeletal':return /gingiva/i.test(n)?'rest':'bone';
  case 'integumentary':return 'skin';
  case 'arterial':return 'arterial';
  case 'venous':return 'venous';
  default:return 'rest';
 }
}
