# Similarity Scorecard

This document explains how close the reproduction is to the original paper's
numerical result.

The score measures numerical similarity, not visual styling. Line width, color,
marker choice, layout, and 3D camera angle are not counted as scientific
mismatches when the underlying numerical feature matches.

## Case Score

- Overall score:
- Similarity level:
- Short explanation:

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
| T000 | 1.0 | `/50` - reason | `/35` - reason | `/15` - reason |  |

## Evaluation Metadata

| Figure/Table/Panel | Stage | Parameter match | Critical | Role | Artifact pass | Data-backed | Manual interventions | Failure type |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| T000 | exploratory/final_reproduction | paper_exact/reduced_scale/... | true | main_claim | true | true | 0 | none |

`final_reproduction` is allowed only when the target uses the original paper
parameters and records an auditable paper-vs-generated parameter mapping.
Small-system, coarse-grid, subset, and proxy runs must remain `exploratory`.

## Render Acceptance

Declare every comparable scientific crop before inspecting its score. Do not
average away a weak subplot.

| Target | Pixel target | Role | Metric | Score | Band | Evidence |
| --- | --- | --- | --- | ---: | --- | --- |
| T000 | PXT000 | primary_scientific_region | pixel_similarity_score_0_100 |  | high_fidelity / accepted / needs_repair / rejected | outputs/checks/pixel_evidence.json |

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
| T000 | What prevents acceptance now | Why that condition exists; confirmed/probable/open | confirmed / not found after 2+ checks / not excluded / not applicable | Exact panels, curves, points and completion ratio | Action, success criterion, evidence to produce |

The machine-readable `evaluation.causal_diagnosis` must also include evidence
for both causes, the concrete code checks, and at least one distinct alternative
hypothesis. A paper discrepancy remains open/probable here; only fresh-context
fresh-context claim-level review may classify a paper-error candidate.

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

- TBD

## Machine-Readable Record

The matching JSON record should live at:

```text
outputs/checks/similarity_scorecard.json
```
