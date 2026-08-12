# Similarity Scorecard

## Case Score

- Overall score: **83.4 / 100**
- Similarity level: `numerical_feature_reproduction`
- Scored targets: `10`
- Critical targets: `4`, all passed
- Data-backed artifacts: `10/10`
- Final-reproduction ready: `false`

The score measures scientific similarity, not plot styling. It is capped by the declared `paper_subset` parameter match, formula provenance, and the type of original-paper reference available.

## Scoring Model

Each target receives up to 50 points for feature match, 35 for numeric closeness, and 15 for paper-scope coverage. The harness then applies evidence caps:

- `paper_subset`: maximum 89;
- `visual_feature_contract`: maximum 80;
- `analytic_reference`: maximum 90;
- `table_exact`: maximum 100;
- formulas containing source-only steps: maximum 89.

## Target Scores

| Target | Weight | Feature | Numeric | Scope | Final score | Main evidence |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| T001 Fig. 1(c) | 2.00 | 50/50 | 34/35 | 15/15 | **89** | rescue `>0.998`; large-N error `<0.002` |
| T002 Fig. 2(a,b) | 2.00 | 50/50 | 28/35 | 15/15 | **80** | unit rescue efficiency and size-degrading dephasing |
| T003 Fig. 2(c,d) | 1.50 | 50/50 | 32/35 | 15/15 | **80** | transient bright peak and printed endpoints |
| T004 Fig. 3 | 1.50 | 50/50 | 33/35 | 15/15 | **80** | N=6 thermal boundary and N-dependent inversion |
| T005 Fig. S1 | 0.75 | 48/50 | 25/35 | 15/15 | **80** | correct site-N ranking; peak-gap offset |
| T006 Table S1 | 0.75 | 50/50 | 30/35 | 15/15 | **89** | 7/7 verdicts; MAE `0.00615` |
| T007 Table S2 | 0.75 | 50/50 | 34/35 | 15/15 | **89** | MAE `0.00182` |
| T008 Fig. S2 | 0.75 | 50/50 | 34/35 | 15/15 | **89** | published log/power fits recovered |
| T009 Fig. S3 | 0.50 | 50/50 | 27/35 | 15/15 | **80** | rescue-specific bright transient |
| T010 Fig. S4 | 0.75 | 50/50 | 32/35 | 10/15 | **80** | correct N=64 boundary on reduced grid |

Weighted score: `83.4`.

## Why The Score Is Not Higher

1. Author random seeds, the mean hopping, exact initial-state notation, and optimization grids are not published; every target is therefore `paper_subset` and `exploratory`.
2. Six curve-based targets have only source rasters plus textual feature anchors, which caps them at 80.
3. T010 uses 5 realizations on a `9x9` grid rather than the paper's 15-realization map.
4. T005 reproduces the site-N ranking, but its peak difference is `-0.080` versus the paper's `-0.044`.
5. T011/QCLE is deferred because required inputs are missing and is not included in the weighted score.

## Machine-Readable Record

The authoritative target metadata, caps, reasons, physics assertions, and weighted result are in:

```text
outputs/checks/similarity_scorecard.json
```
