# Similarity Scorecard

This document explains how close the reproduction is to the original paper's
numerical result. The score measures numerical similarity, not visual styling.

## Case Score

- Overall score: **90.0 / 100**
- Similarity level: **complete_reproduction**
- Short explanation: Fig. 2 (both panels) is reproduced from the paper's own
  closed-form expressions at the published figure-legend parameters, matching the
  degeneracy ladders and the thermodynamic curves exactly; the physics behind it
  (emergent free paraparticles, `z_R=1+m x`) is independently confirmed by exact
  diagonalization of the 1D solvable spin model to machine precision. Both targets
  are capped at 90 by the `analytic_reference` comparison tier (the Nature figure
  is raster-only, so there is no author-data table to match pointwise).

## Scoring Model

Each in-scope numerical target is scored out of 100: feature match (50), numeric
closeness (35), paper-scope coverage (15).

## Figure Scores

| Figure/Table/Panel | Weight | Feature match | Numeric closeness | Paper-scope coverage | Score |
| --- | ---: | --- | --- | --- | ---: |
| T1 — Fig. 2 (exclusion statistics + thermodynamics) | 0.8 | 49/50 — both panels feature-for-feature | 34/35 — same analytic functions, limits to 1e-9 | 15/15 — paper-exact legend params | 90.0 |
| T2 — 1D solvable spin-model ED (validation) | 0.2 | 48/50 — free-paraparticle spectrum & conserved number | 35/35 — max dev ~1e-14 | 13/15 — exact model, illustrative N, 1D only | 90.0 |

## Evaluation Metadata

| Target | Stage | Parameter match | Critical | Role | Artifact pass | Data-backed | Manual interv. | Failure type | Reference | Provenance | Formula gate |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| T1 | final_reproduction | paper_exact | true | main_claim | true | true | 0 | none | analytic_reference | analytic_reference | verified |
| T2 | final_reproduction | paper_exact | false | method_validation | true | true | 0 | none | analytic_reference | independent_numerics | verified |

## Interpretation

- `90-100`: complete reproduction.
- `60-89`: numerical feature reproduction.
- `0-59`: feature not accepted as reproduced.

## What Prevents A Higher Score

- The Nature figure is raster-only with no author data table, so the strongest
  available reference is `analytic_reference` (cap 90). Since both the paper's
  Fig. 2 and this reproduction are the same closed-form functions and are verified
  independently by ED, this cap is a provenance formality, not a physics gap.
- The 2D solvable KDH model, its 8-body plaquette terms, and the braiding
  demonstration (Methods/SI) are out of scope for this case.

## Machine-Readable Record

`outputs/checks/similarity_scorecard.json`
