# Similarity Scorecard

This document explains how close the reproduction is to the original paper's
numerical result.

The primary score is direct pixel difference in each predeclared scientific
region, but only after formula, provenance, execution, and physics gates pass.
Presentation settings may be tuned only in the post-freeze RenderContract.

## Case Score

- Overall score: 86.79/100
- Similarity level: `numerical_feature_reproduction`
- Short explanation: all five historical display targets pass formula,
  provenance, execution, and physics checks. Four scientific regions pass the
  render threshold; T002 carries an explicit paper-subset cap. T006 is a new
  zero-weight uncovered claim contract and therefore does not rewrite the
  historical aggregate.

The public whole-paper measure is separate from that historical five-target
render score: coverage is 97.83% (`45/46`), covered-item fidelity is 87.56, and
the reproduction degree is 85.66/100. The one zero-scored uncovered item is
listed explicitly below rather than averaged away or silently omitted.

## Scoring Model

Each in-scope numerical figure, table, or panel is scored out of 100:

- feature match: 50 points;
- numeric closeness: 35 points;
- paper-scope coverage: 15 points.

Each component must include a reason. The case score is the weighted average of
targets with a comparable declared primary metric. A critical target may be
excluded from aggregation only with `score_aggregation=excluded` and an
explicit `score_exclusion_reason`; it remains required for lifecycle
completion.

## Figure Scores

| Figure/Table/Panel | Weight | Feature match | Numeric closeness | Paper-scope coverage | Score |
| --- | ---: | --- | --- | --- | ---: |
| T001 | 1.0 | 45.00/50 | 31.50/35 | 13.50/15 | 90.00 |
| T002 | 1.0 | 38.58/50 | 27.01/35 | 11.57/15 | 77.16 |
| T003 | 1.0 | 45.00/50 | 31.50/35 | 13.50/15 | 90.00 |
| T004 | 1.0 | 45.00/50 | 31.50/35 | 13.50/15 | 90.00 |
| T005 | 1.0 | 43.38/50 | 30.37/35 | 13.02/15 | 86.77 |
| T006 | 0.0, excluded | 0.00/50 | 0.00/35 | 0.00/15 | 0.00 |

The three 90-point targets are capped by the `analytic_reference` evidence tier;
they are not claims of pixel identity. Component rounding is reconciled so each
row sums to its displayed target score.

## Evaluation Metadata

| Figure/Table/Panel | Stage | Parameter match | Critical | Role | Artifact pass | Data-backed | Manual interventions | Failure type |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| T001 | final_reproduction | paper_exact | true | main_claim | true | true | 0 | none |
| T002 | exploratory | paper_subset | true | main_claim | true | true | 0 | missing_parameters |
| T003 | final_reproduction | paper_exact | true | main_claim | true | true | 0 | none |
| T004 | final_reproduction | paper_exact | true | main_claim | true | true | 0 | none |
| T005 | final_reproduction | paper_exact | true | main_claim | true | true | 0 | none |
| T006 | exploratory | paper_exact | false | supporting | false | false | 0 | source_discrepancy |

`final_reproduction` is allowed only when the target uses the original paper
parameters and records an auditable paper-vs-generated parameter mapping.
Small-system, coarse-grid, subset, and proxy runs must remain `exploratory`.

## Render Acceptance

Declare every comparable scientific crop before inspecting its score. Do not
average away a weak subplot.

| Target | Pixel target | Role | Metric | Score | Band | Evidence |
| --- | --- | --- | --- | ---: | --- | --- |
| T001 | PXT_T001_MAIN | primary_scientific_region | pixel_similarity_score_0_100 | 94.5095 | high_fidelity | outputs/checks/pixel_evidence.json |
| T002 | PXT_T002_SPECTRUM | primary_scientific_region | pixel_similarity_score_0_100 | 77.1628 | needs_repair | outputs/checks/pixel_evidence.json |
| T003 | PXT_T003_SCALING | primary_scientific_region | pixel_similarity_score_0_100 | 94.5205 | high_fidelity | outputs/checks/pixel_evidence.json |
| T004 | PXT_T004_BOUNDS | primary_scientific_region | pixel_similarity_score_0_100 | 90.0545 | high_fidelity | outputs/checks/pixel_evidence.json |
| T005 | PXT_T005_REGIMES | primary_scientific_region | pixel_similarity_score_0_100 | 86.7662 | accepted | outputs/checks/pixel_evidence.json |

- `>=90`: highly faithful and passed.
- `>=80`: accepted and passed.
- `>=65, <80`: RenderContract repair required.
- `<65`: rejected.
- Full-canvas rows use `full_canvas_diagnostic`; they never decide completion.
- If registration is genuinely meaningless, set `pixel_status=not_comparable`
  and provide both `pixel_status_reason` and non-empty
  `pixel_alternative_evidence`.
- RenderContract work may change only layout/style/interpolation. It must not
  change formulas, physical parameters, numerical code, or generated arrays.

## Causal Diagnosis For Every Problem Target

Use scorecard schema v4. Do not stop at a `failure_type` label. For every target
with a remaining limitation, record:

| Target | Direct cause | Root cause + confidence | Is our code at fault? | Affected scope | Next discriminating test |
| --- | --- | --- | --- | --- | --- |
| T002 | Complete-window spectrum crop is 77.16 and the exact plotted level subset is not published | publication underspecification, confirmed | no remaining kernel fault after four distinct checks | Fig. 2(a) paper-exact attribution and pixel acceptance | obtain primary-source level-selection metadata and rerun without importing curve coordinates |
| T006 | Eq. (15) evaluates to `0.105723838752` at `f=0.5`, but the following prose says about `0.14`; no independent scalar artifact exists | unresolved, open | not excluded because existing figure code does not evaluate the scalar | one no-display quantitative claim | independent re-derivation, second high-precision implementation, fresh-context review |

The machine-readable `evaluation.causal_diagnosis` must also include evidence
for both causes, the concrete code checks, and at least one distinct alternative
hypothesis. A paper discrepancy remains open/probable here; only fresh-context
protocol-v2 review may classify a paper-error candidate.

Do not author the stop decision. The Harness derives
`causal_diagnosis_disposition`: only a publication omission, an attested
code-ready compute shortfall, an unavailable external dependency, a stable
paper discrepancy after fault exclusion, or an explicit user descope can be a
`terminal_blocker`. Code/method/evidence/review/scope defects and unresolved
attribution are `react_loop_required` and must be repaired or tested again.

## Interpretation

- `90-100`: top similarity tier (historical enum `complete_reproduction`; not lifecycle completion).
- `60-89`: numerical feature reproduction.
- `0-59`: feature not accepted as reproduced.

## What Prevents A Higher Score

- T002 uses the exact axis box and its line density is within 2.1% after
  post-freeze interpolation to the author EPS sampling density. The residual
  cannot be closed scientifically because the plotted level subset/cutoff is
  not declared; source-curve coordinates remain forbidden as numerical input.
- T005 is accepted at 86.77. Its distance from the optional 90-point
  high-fidelity band is diagnostic only and does not open a repair loop.
- T006 is explicitly uncovered. Its source-internal mismatch is real, but its
  root cause and paper-error status remain unresolved until independent review.
- No fresh-context scientific reviewer has yet tried to falsify the result.

## Machine-Readable Record

The matching JSON record should live at:

```text
outputs/checks/similarity_scorecard.json
```
