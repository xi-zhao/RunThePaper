# Consistency Report

This file states which outputs match the paper and which do not.

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | The paper publishes curves rather than reusable numeric arrays. |
| feature_match | 3 | T001, T003, and T004 pass the repaired v6 scientific checks. |
| partial_match | 1 | T002 contains every excitation in the printed energy window, but the paper does not publish the subset selected for display. |
| stable_discrepancy | 1 | T005 exposes an Eq. (15)-versus-prose inconsistency at `f=0.5`. |
| input_match_only | 0 | Inputs match, outputs still differ. |
| blocked | 0 | Missing information prevents exact validation. |
| not_in_scope | 0 | Schematic, experimental, or external context. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Fig. 1 + inset | feature_match | `science_checks.json`, `fig1_kink_density.csv` | Prefactor 0.17889 versus paper fit near 0.16; exponent 0.58069 versus 0.58. | Finite-size/grid and printed-fit precision. |
| T002 | Fig. 2(a) | partial_match | `science_checks.json`, `fig2a_spectrum.csv` | The repaired inventory contains all 2,607 branches from particle sectors 0 through 6 that enter the printed `E/W <= 6.1` window; the scientific-region render score is 77.16. | The former two-particle truncation was a reproduction defect and is fixed. The remaining gap is publication underspecification: the paper does not enumerate the displayed subset of the “lowest excitations.” |
| T003 | Fig. 2(b) | feature_match | `science_checks.json`, `fig2b_fidelity_scaling.csv` | Direct root solving leaves a maximum crossing residual of `1.74e-8`; the declared asymptotic `N >= 40` fit gives exponent 1.93365 versus the paper's 1.93. | The former sparse-interpolation and fit-window defects are fixed. |
| T004 | Fig. 2(c) | feature_match | `science_checks.json`, `fig2c_fidelity_bounds.csv` | No bound violation observed. | No unresolved scientific mismatch. |
| T005 | Fig. 3 + inset | stable_discrepancy | `science_checks.json`, `fig3_kink_count.csv` | Eq. (15) gives 0.10572384 at `f=0.5`, the following prose says 0.14, and independent dynamics gives about 0.1529. | Stable formula-versus-prose branch/prefactor inconsistency; independently reviewed paper-error candidate. |

## Paper Review

The previous fresh-context protocol-v2 review is historical: it correctly
found the old T002 truncation and T003 interpolation defects, but v6 changed the
scientific data and repaired both defects. It must therefore not be reused as a
current independent decision. T005 retains a stable formula-versus-prose
discrepancy, but its previous `paper_error_candidate` decision also requires a
new review against the v6 bundle. `PAPER_ASSESSMENT.md` and the old reviewer
submission remain immutable historical evidence rather than current authority.
