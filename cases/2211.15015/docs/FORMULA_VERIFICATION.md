# Formula verification

The machine gate is `outputs/checks/formula_verification.json`.

- EQ001–EQ005 and EQ007–EQ009 are verified against the printed equations and independent identities.
- EQ006 (post-T1 reset geometry) is reconstructed because the paper does not print the reset separation.
- EQ010 (collapse-analysis details) is reconstructed because exact fitting windows and the full shear grid are not printed.
- The energy-gradient force was checked by central finite differences with maximum absolute error below `4e-10` in the development test.
- Uniform polarization reproduces the printed Eq. (5) normalization, yielding active force `v/6` per vertex for the exact printed weights.
- Translation invariance, zero net polygon force, passive energy descent, and torus topology provide independent limiting/invariant checks.

Reconstructed formulas remain open for numerical exploration but prevent a paper-exact scientific claim.
