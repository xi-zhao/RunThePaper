# Similarity Scorecard

The score combines scientific feature checks, numerical/primary-pixel
closeness, and declared paper-scope coverage. Source-figure evidence caps a
target at 70 independently of how similar its layout looks.

## Case Score

- Overall score: `61.32/100`
- Similarity level: `numerical_feature_reproduction`
- Short explanation: six scientific assertions pass; T005 fails its essential
  paper-consistency assertion and T007 is a missing-parameter proxy.
- Primary raw pixel metric: scientific-theory-region symmetric F1,
  `59.6688/100` over T001--T006
- Full-canvas diagnostic: `93.2922/100`

## Figure Scores

| Target | Weight | Feature match | Numeric closeness | Scope coverage | Final capped score |
| --- | ---: | --- | --- | --- | ---: |
| T001 | 1.0 | 42/50 — collapse field matches | 29.11/35 — pixel F1 83.1590 | 15/15 | 70.00 |
| T002 | 1.0 | 46/50 — phase boundary rises correctly | 33.28/35 — pixel F1 95.0859 | 15/15 | 70.00 |
| T003 | 1.0 | 43/50 — ratio/band behavior matches | 15.04/35 — pixel F1 42.9675 | 15/15 | 70.00 |
| T004 | 1.0 | 46/50 — both critical-number anchors match | 23.31/35 — pixel F1 66.5958 | 15/15 | 70.00 |
| T005 | 1.0 | 25/50 — branch ordering disagrees | 9.23/35 — pixel F1 26.3797 | 7.5/15 | 41.73 |
| T006 | 1.0 | 48/50 — paper-exact levitation feature | 15.34/35 — pixel F1 43.8251 | 15/15 | 70.00 |
| T007 | 1.0 | 30/50 — qualitative suppression only | 0/35 — proxy curves do not overlap | 7.5/15 | 37.50 |

## Evaluation Metadata

| Target | Stage | Parameter match | Critical | Role | Artifact pass | Data-backed | Manual interventions | Failure type |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| T001 | exploratory | paper_subset | true | main_claim | true | true | 0 | not_paper_parameters |
| T002 | exploratory | paper_subset | true | main_claim | true | true | 0 | not_paper_parameters |
| T003 | exploratory | paper_subset | true | supporting | true | true | 0 | not_paper_parameters |
| T004 | exploratory | paper_subset | true | main_claim | true | true | 0 | not_paper_parameters |
| T005 | exploratory | paper_subset | true | main_claim | true | true | 0 | model_mismatch |
| T006 | final_reproduction | paper_exact | true | method_validation | true | true | 0 | none |
| T007 | exploratory | proxy_model | true | supporting | true | true | 0 | missing_parameters |

Artifact pass means the declared calculation ran and produced valid evidence;
it does not turn T005's failed scientific assertion or T007's proxy into a
paper match.

## What Prevents A Higher Score

- T001--T005 cannot be paper-exact without the target paper's coupled-channel
  interaction model.
- T005 has a stable but inconclusive branch-order difference; the theory-width
  functional and paper-exact interaction lane are missing.
- T007's frozen result is a scaling proxy and lacks the calibration atom
  number; a method-faithful 3D GPE lane is code-ready.
- Main Fig. 4's 3D method is code-ready, but paper-exact agreement is deferred
  because the per-curve atom numbers are unpublished.
- Fresh-context independent review is still missing.

## Machine-Readable Record

`outputs/checks/similarity_scorecard.json`
