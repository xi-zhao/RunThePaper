# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 1 | Fig. 2 lattice and analytic observables agree under all declared checks. |
| feature_match | 1 | Fig. 3 curve geometry agrees under the formula-derived 0–5 interpretation; its conflict with the printed labels remains inconclusive. |
| partial_match | 0 | No numerical target is partial. |
| unavailable | 0 | No numerical target is limited by compute or data. |
| not_in_scope | 1 | Main Fig. 1 is a conceptual schematic. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 2 | exact_match | `outputs/checks/target_checks.json`; `outputs/checks/pixel_evidence.json` | Minor font and rasterization differences | Independent plotting stack. |
| T002 | Main Fig. 3 | feature_match | `outputs/checks/target_checks.json`; `outputs/checks/figure3_legend_audit.json` | Reproduction labels final branches 4,5; paper prints 5,6 | Stable label/curve discrepancy; `inconclusive` pending protocol-v2 review. |

All eight numerical invariants in `target_checks.json` pass. The accepted run
records zero forbidden source accesses. The direct scientific-region pixel
scores are 99.4359 and 95.1851.

## Paper-review boundary

The Fig. 3 discrepancy is not a reproduction failure, but the existing evidence
also does not authorize a paper-error claim. A successful paper-scale rerun is
execution evidence only. `paper_error_candidate` additionally requires strict
paper-reference quantification, convergence, two distinct independent checks,
an explicit falsification attempt, and a fresh protocol-v2 reviewer. None of the
case-local scripts may emit that classification.
