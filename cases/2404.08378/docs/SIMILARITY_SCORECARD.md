# Similarity Scorecard

## Case score

- Overall score: `65.0/100`.
- Similarity level: `numerical_feature_reproduction`.
- Aggregation: 18 targets, equal weight, all included.
- Meaning: the independently generated scientific features are credible, but the case is not a complete paper-exact reproduction.

The score measures the scientific numerical object. Published pixels are never inputs to numerics and no geometrically registered pixel score is claimed. Post-freeze source/reproduction boards are diagnostic evidence only.

## Target scores

| Targets | Parameter match | Score | Reason |
| --- | --- | ---: | --- |
| T002–T008, T010–T013, T015 | `paper_exact` | 70 each | formula/model features pass; source reference is figure-only and fresh review is missing |
| T001, T014, T016 | `proxy_model` | 55 each | scientific trend reproduced but indispensable solver/spectral details are unpublished |
| T009, T017, T018 | `paper_subset` | 55 each | printed scalar feature is reproduced but point arrays or conventions are incomplete |

## Why the score is not higher

- Nine experimental point arrays are unavailable; no image digitization is permitted.
- Vector-FEM mesh, boundary conditions and complete material model are unavailable.
- Spectral HOM weighting lacks the measured reflectivity/grating arrays.
- Brightness and HOM-width statements use rounded values or unstated conventions.
- The comparison lane has no declared geometric registration, so source pixels cannot supply a numeric-closeness claim.
- Fresh-context independent review has not yet validated or falsified the target inventory.

The machine-readable record is `outputs/checks/similarity_scorecard.json`. It contains per-target formulas, evidence, caps, essential assertions and remaining gaps.
