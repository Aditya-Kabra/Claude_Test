# PBPK Atlas (source)

A whole-body, perfusion-limited PBPK model drawn on the [Human Atlas](https://github.com/ashemag/human-atlas)
3D anatomy (MIT; BodyParts3D geometry CC BY 4.0). Each mesh is coloured by the drug concentration
in its compartment. You can scrub or play through time, change the compound and dosing, and
compare plasma with any tissue.

- `app/pbpk/physiology.ts`: ICRP 89 reference-male volumes, flows and tissue composition
- `app/pbpk/model.ts`: Poulin–Theil Kp prediction, the ODE system (RK4) and exposure metrics
- `app/pbpk/mapping.ts`: which BodyParts3D mesh belongs to which compartment
- `app/pbpk/drugs.ts`: illustrative presets (midazolam, caffeine, diazepam, warfarin)
- `app/scene.tsx`: the Human Atlas viewer, extended with a per-part heat texture and mask

```sh
npm ci
npm run test:pbpk   # mass balance, AUC = dose/CL, oral F
npm run check
npm run build       # writes ../pbpk-atlas, which GitHub Pages serves
```

The built page loads geometry from `../human-atlas/models/`, so both folders must be deployed
together. This is an educational model, not validated for clinical use.
