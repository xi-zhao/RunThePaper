# Formula Verification

All six formula objects are source-traced, independently checked, and open for
numerical use. The machine gate is
`outputs/checks/formula_verification.json` and currently passes.

| Formula | Role | Gate | Independent check and use |
| --- | --- | --- | --- |
| EQ001 | squeezing-dependent coupling | open / verified | exact hyperbolic limits; T001 |
| EQ002 | steady-state battery energies | open / verified | energy identity, author arrays, and S3 normalization limit; T002C, T003, TS03 |
| EQ003 | coupling derivatives | open / verified | symbolic derivative and finite differences; T003, TS02 |
| EQ004 | forward transmission | open / verified | scattering reduction and optimum; T004 |
| EQ005 | affine Gaussian moments | open / verified | independent ODE/exponential solvers and finite-Fock audit; T002A, TS01 |
| EQ006 | passive energy and ergotropy | open / verified | symplectic invariant and positivity limits; T002D, TS04 |

## Source Cautions

- Figure 1(c) leaves the absolute `r` scale symbolic. The renderer uses `r=1`
  while testing identities for arbitrary `r`.
- The main-text EQ004 TeX has a brace typo; the supplemental scattering matrix
  fixes the intended cosine term unambiguously.
- The released transmission arrays are from an earlier manuscript version and
  do not alter the final-paper EQ004 gate.
- Figure S3 is labeled `E_i^ss/omega_b`, but all visible curves start at one.
  EQ002 gives unequal absolute `r=0` baselines and exactly unit normalized
  baselines, so TS03 is generated as `E_i^ss/E^ss`; both forms remain in the
  output data for audit. Author confirmation remains unavailable.
- Figure S1 reports finite-Hilbert numerics without a cutoff or convergence
  study. EQ005 remains verified; the paper's quantitative S1 result is rejected.

## Run

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/2607.00718 --write
```
