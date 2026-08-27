# Similarity Scorecard

## Case Score

- Overall scientific score: `90.0/100`
- Similarity level: `complete_reproduction`
- Pixel-fidelity score: `89.89/100`
- Status: all scientific and pixel contracts passed

## Scoring Model

Each target receives 50 points for features, 35 for quantitative closeness, and
15 for paper-scope coverage. Both raw component totals are 100. The frozen
bundle provides analytic formulas and vector plots but no author data table, so
the `analytic_reference` evidence policy caps each scientific target at 90.

## Figure Scores

| Figure/Table/Panel | Weight | Feature match | Numeric closeness | Paper-scope coverage | Score |
| --- | ---: | --- | --- | --- | ---: |
| T001 / Fig. 2(a,b) | 1.0 | 50/50 — signs, ordering and limiting behavior pass | 35/35 — two representations agree to `2.09e-11` | 15/15 — two panels, four masses, full ranges | 90.0 |
| T002 / Fig. 3 | 1.0 | 50/50 — divergence, ordering and approach to one pass | 35/35 — ratio oracle agrees to `2.12e-12` | 15/15 — four masses and full range | 90.0 |

## Evaluation Metadata

| Figure/Table/Panel | Stage | Parameter match | Critical | Role | Artifact pass | Data-backed | Manual interventions | Failure type |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| T001 | final_reproduction | paper_exact | true | main_claim | true | true | 0 | none |
| T002 | final_reproduction | paper_exact | true | main_claim | true | true | 0 | none |

## What Prevents A Higher Score

- No official author curve data or tabulated values are present.
- Reproducing the displayed integrals cannot remove the upstream factor-two
  spectrum inconsistency.

Neither issue is hidden by relaxed thresholds. All six essential physics
assertions pass.

## Machine-Readable Record

- Scientific: `outputs/checks/similarity_scorecard.json`
- Pixel: `outputs/checks/pixel_evidence.json`
- Coverage: `outputs/checks/figure_coverage_check.json`
