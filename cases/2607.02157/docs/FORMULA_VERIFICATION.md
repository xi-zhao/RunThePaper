# Formula Verification

This document explains which formulas are allowed to feed numerical reproduction.

Machine-readable result:

```text
outputs/checks/formula_verification.json
outputs/checks/formula_check_details.json
```

Run:

```bash
python code/scripts/verify_formulas.py
```

## Status

All 15 equation cards are independently checked and open (gate `passed`,
15/15). The verification suite contains 17 machine checks
(`formula_check_details.json`).

- Verified with independent re-derivation + numeric checks
  (`source_and_symbolic`): EQC001 (collisional map CPTP/Gibbs invariance),
  EQC003/EQC004 (Holevo recast + ensemble marginalization), EQC006/EQC007
  (coherence decomposition and QID split), EQC009 (beta*W_irr = chi_d, exact),
  EQC010 (relaxation monotonicity), EQC011 (BKM kernel + quadratic expansion),
  EQC012 (G-resonance peak ~2.3), EQC015 (coherence convexity bound).
- Formerly source-only definitions now carry independent checks: EQC002
  (drive statistics and spectral peak), EQC005 (shared-entropy cancellation),
  EQC008 (law-of-total-expectation work identity), EQC013 (duality and spectral
  boundary fingerprints), and EQC014 (ridge normal equations and objective
  minimum).

## Open assumptions that feed numerics

1. EQC002: drive normalization calibrated to the paper's published statistics
   (centered, sigma_s^2 = 0.11) because the verbal min-max description
   contradicts them. Affects capacity amplitudes only through the drive
   variance the paper itself reports.
2. EQC013: the unpublished cluster-chain boundary is resolved to open.
   Periodic boundaries would impose an exact alpha -> 1-alpha duality that
   contradicts the paper's asymmetric curves; the open-chain spectrum also
   matches Fig. S1c.
3. Fig. S1a F(omega) plot normalization assumed (|FFT|^2 * 2pi / N^2); the
   paper publishes neither the formula nor units.
4. EQC014: the paper does not state whether the linear readout contains a
   constant bias feature; the reproduction includes one.
