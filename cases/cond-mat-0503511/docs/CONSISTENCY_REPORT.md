# Consistency Report

This file states which outputs match the paper and which do not.

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | The paper publishes curves rather than reusable numeric arrays. |
| feature_match | 4 | T001, T003, T004, and the existing T005 display target pass the repaired v6 scientific checks. |
| partial_match | 1 | T002 contains every excitation in the printed energy window, but the paper does not publish the subset selected for display. |
| uncovered_source_discrepancy | 1 | T006 isolates the Eq. (15)-versus-prose inconsistency at `f=0.5`; its root cause remains open. |
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
| T005 | Fig. 3 | feature_match | `science_checks.json`, `fig3_kink_count.csv` | The six numerical curves and their KZM/LZF regimes are artifact-backed; fresh review and the fastest-rate plateau remain separate W2 questions. | Existing target-level science checks pass; this row no longer carries the independent no-display Eq. (15) scalar claim. |
| T006 | Eq. (15) and following prose | uncovered_source_discrepancy | `paper-source/article.tex`, `figure_coverage.json` | Literal Eq. (15) gives `0.105723838752` at `f=0.5`, while the prose says approximately `0.14`; no independent claim artifact exists. | Root cause unresolved; convention, transcription, reproduction-method, and paper-error hypotheses require independent re-derivation. |

## Paper Review

The previous fresh-context protocol-v2 review is historical: it correctly
found the old T002 truncation and T003 interpolation defects, but v6 changed the
scientific data and repaired both defects. It must therefore not be reused as a
current independent decision. W1 now isolates the formula-versus-prose scalar as
T006 and marks it uncovered with an open root cause; any previous T005
`paper_error_candidate` decision also requires a new review against the v6
bundle. `PAPER_ASSESSMENT.md` and the old reviewer submission remain immutable
historical evidence rather than current authority.
