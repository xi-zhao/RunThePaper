# Formula Verification

This document explains which formulas are allowed to feed numerical reproduction.

Machine-readable result:

```text
outputs/checks/formula_verification.json
outputs/checks/formula_check_details.json
```

Run:

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/2607.02157 --write
python case/2607.02157/scripts/verify_formulas.py   # from workspace: scripts/verify_formulas.py
```

## Status

All 15 equation cards are open (gate `passed`, 15/15). Verification suite:
14/14 numeric checks pass (`formula_check_details.json`).

- Verified with independent re-derivation + numeric checks
  (`source_and_symbolic`): EQC001 (collisional map CPTP/Gibbs invariance),
  EQC003/EQC004 (Holevo recast + ensemble marginalization), EQC006/EQC007
  (coherence decomposition and QID split), EQC009 (beta*W_irr = chi_d, exact),
  EQC010 (relaxation monotonicity), EQC011 (BKM kernel + quadratic expansion),
  EQC012 (G-resonance peak ~2.3), EQC015 (coherence convexity bound).
- Definitions taken from the paper (`source_only`): EQC002 (Mackey-Glass
  drive), EQC005 (QID definition), EQC008 (injection work), EQC013 (model
  Hamiltonians; PBC assumption checked via gap closing at alpha = 0.5),
  EQC014 (ridge/NMSE).

## Open assumptions that feed numerics

1. EQC002: drive normalization calibrated to the paper's published statistics
   (centered, sigma_s^2 = 0.11) because the verbal min-max description
   contradicts them. Affects capacity amplitudes only through the drive
   variance the paper itself reports.
2. EQC013: cluster chain assumed periodic; supported by the alpha = 0.5 gap
   closing and by Fig. S1c comparison.
3. Fig. S1a F(omega) plot normalization assumed (|FFT|^2 * 2pi / N^2); the
   paper publishes neither the formula nor units.
