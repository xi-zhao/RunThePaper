# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 1 | Analytic spin-1 identities match the paper-derived reference. |
| feature_match | 9 | Independent numerics reproduce the source-figure features. |
| partial_match | 0 | No target has partial generation coverage. |
| input_match_only | 0 | Every configured target produced checked outputs. |
| blocked | 0 | A100 unavailability did not block the paper scale. |
| not_in_scope | 1 | No table exists in the source. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 1 | exact_match | `t001_spin1_foliation.json` | 3D camera/style | Author plotting metadata absent. |
| T002 | Main Fig. 2 left | feature_match | `t002_figure.json`, comparison board | No pointwise residual | Author arrays absent; shell convention omitted. |
| T003 | Main Fig. 2 right | feature_match | `t003_dynamics.json`, comparison board | Band widths are not pointwise reference-checked | Confidence algorithm omitted. |
| T004 | Fig. S1 | feature_match | `t004_figure.json` | No pointwise residual | Author arrays absent. |
| T005 | Fig. S2 | feature_match | `t005_figure.json` | No pointwise residual | Author arrays absent. |
| T006 | Fig. S3 | feature_match | `t006_figure.json` | No pointwise residual | Author arrays absent. |
| T007 | Fig. S4 | feature_match | `t007_figure.json` | No pointwise residual | Author arrays absent. |
| T008A | Fig. S5 row 1 | feature_match | `t008a_figure.json` | Scatter points not paired | Author arrays absent. |
| T008B | Fig. S5 row 2 | feature_match | `t008b_figure.json` | Scatter points not paired | Author arrays absent. |
| T009 | Fig. S6 | feature_match | `t009_figure.json` | Values visually rather than table-matched | Author table absent. |

## Cross-Artifact Consistency

- All reader-facing figures read case-local CSV/JSON; source images are used
  only in side-by-side boards.
- `TARGET_LEDGER.md`, `figure_coverage.json`, per-target checks, and the
  similarity scorecard identify the same ten executable targets.
- All static shards record periodic boundaries, centred shells, and independent
  numerics.
- T003 records all 214 shell representatives and the same published
  Hamiltonians used by T002/T008A/T009.
- The score `72.05` is conservative: the source-reference cap, not missing
  generation scope, limits nine targets.
