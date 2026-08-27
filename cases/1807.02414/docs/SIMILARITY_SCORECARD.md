# Similarity Scorecard

## Target-level fidelity

| Target | Feature | Numeric | Scope | Evidence cap | Final score |
| --- | ---: | ---: | ---: | ---: | ---: |
| T001 Main Fig. 1 GHD theory | 48/50 | 32.72/35 | 15/15 | 70 (reduced operator/source-figure reference) | 70.00 |
| T002 printed diffusion values | 49/50 | 34.72/35 | 15/15 | 100 | 98.72 |
| T003 tDMRG marker series | 0/50 | 0/35 | 0/15 | ungenerated | 0.00 |
| T004 hard-rod limit | 0/50 | 0/35 | 0/15 | unimplemented | 0.00 |
| T005 free-model zero diffusion | 0/50 | 0/35 | 0/15 | unimplemented | 0.00 |
| T006 entropy-production positivity | 0/50 | 0/35 | 0/15 | unimplemented | 0.00 |

The historical covered-target quality mean remains **84.36/100** for T001 and
T002. It is not the whole-paper coverage claim.

## Whole-paper item metrics

- Eligible atomic items: **13**.
- Covered items: **7**.
- Uncovered items: **6**.
- Coverage: **53.85%**.
- Covered-item fidelity: **74.07/100** = `(6 x 70 + 98.49) / 7`.
- Whole-paper reproduction degree: **39.88/100** =
  `(6 x 70 + 98.49 + 6 x 0) / 13`.

Here `98.49` is the Harness v1 item-fidelity projection for T002; the legacy
target scorecard's component total remains 98.72. Public whole-paper metrics
use the authoritative item projection, not the legacy target aggregate.

Uncovered items are not hidden behind the aggregate: tDMRG at t=10, t=20 and
t=40; the hard-rod limiting claim; the free-model zero-diffusion claim; and the
entropy-production positivity claim. Their direct/root causes and next tests
are recorded in `FIGURE_CLASSIFICATION.md` and the machine-readable scorecard.

The raw post-freeze scientific pixel metric for T001 is **93.49/100** using a
four-pixel curve F1. It does not override the scientific evidence cap and is
not used for the six uncovered items.

Machine-readable record: `outputs/checks/similarity_scorecard.json`.
