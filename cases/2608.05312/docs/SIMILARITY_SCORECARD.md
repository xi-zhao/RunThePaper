# Similarity Scorecard

## Case Score

- Overall score: **83.52 / 100**
- Similarity level: `numerical_feature_reproduction`
- Aggregate-included targets: `11`
- Declared target contracts: `12` (`11` scored, `1` input-blocked and excluded from the aggregate)
- Eligible atomic items: `72`; covered: `68`; uncovered: `4`
- Item reproduction degree: **78.40 / 100** (`94.44% × 83.02`)
- Critical targets: `4`, all passed
- Data-backed artifacts: `11/11`
- Final-reproduction ready: `false`

The `83.52` score measures similarity among the eleven executed target
contracts, not whole-paper coverage or plot styling. The public whole-paper
measure is the item reproduction degree: uncovered eligible items contribute
zero, while supporting claims already represented by displayed items are not
counted twice.

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
| T011 Fig. S5(a,b) | 0.00 | 0 | 0 | 0 | **uncovered** | four source-blocked QCLE/phenomenological series |
| T012 Fig. S1(b) baseline | 0.25 | 50/50 | 24/35 | 15/15 | **89** | `0.5536 +/- 0.0548` vs paper `0.65`; zero-rate branch attested |

Weighted score: `83.52`.

## Why The Score Is Not Higher

1. Author random seeds, the mean hopping, exact initial-state notation, and optimization grids are not published; every target is therefore `paper_subset` and `exploratory`.
2. Six curve-based targets have only source rasters plus textual feature anchors, which caps them at 80.
3. T010 uses 5 realizations on a `9x9` grid rather than the paper's 15-realization map.
4. T005 reproduces the site-N ranking, but its peak difference is `-0.080` versus the paper's `-0.044`.
5. T011/QCLE remains in the whole-paper denominator with four uncovered items
   because required benchmark inputs are missing; it is excluded only from the
   aggregate.
6. T012 is now covered, but unpublished disorder seeds leave a visible sampling offset and uncertainty.

## Machine-Readable Record

The authoritative target metadata, caps, reasons, physics assertions, and weighted result are in:

```text
outputs/checks/similarity_scorecard.json
```
