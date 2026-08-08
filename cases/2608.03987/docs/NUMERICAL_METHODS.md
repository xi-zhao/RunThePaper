# Numerical Methods

## NUM008 — Figure 8 cost-law scatter

- **Target:** T008 / Figure 8.
- **Equation:** `o = C(T)/V(T) = 1 + 2m + r`.
- **Scale:** all 67 paper circuits: 12 random, 24 Clifford+T, 10 QAOA, 21 VQE.
- **Independent data:** `(m,r,o)` from the full green-aware trees produced by
  METHOD002. No released `(m,r)` values are used in the calculation.
- **Acceptance:** unique circuit IDs and exact family counts; `m,r≥0`,
  `m+r≤1`; every point inside `[1+2m, 2+m]`; law residual `≤1e-9`.
- **Output:** `outputs/data/fig8_cost_law.csv` and four figure formats.

## NUM009 — Figure 9 order-transfer comparison

- **Target:** T009 / Figure 9(a,b).
- **Observable:** `|o_convert-o_full|/o_full`, with an additional audit of
  `|C_convert-C_full|/C_full` so changes in the per-tree skeleton denominator
  cannot masquerade as optimization gains.
- **Pipelines:** minimum-skeleton candidate plus skeleton NNI anneal; the same
  tree with low-temperature real-cost polish; independently selected
  real-cost candidate plus full NNI anneal.
- **Paper threshold:** `5e-4`; left-edge aggregation at `1e-6`.
- **Interpretation rule:** Eq. (8) is an identity and must pass exactly. Figure
  9 is an empirical search-budget statement; optimizer-dependent differences
  are reported rather than forced to match.
- **Output:** `outputs/data/fig9_pipeline.csv`, four figure formats, and
  `outputs/checks/source_comparisons.json`.

## Reproducibility controls

- Archive SHA-256:
  `719bd15ebb4fa4c54a3e8c433577a824956bff37ab480ecc84387649d5aa8b9e`.
- Python, cotengra candidate selection, and case-local NNI use a fixed seed.
- Each final tree stores every child pair and a SHA-256 digest.
- Runner records are resumable and skipped only when configuration and network
  topology hashes both match.
- A tiny exact dynamic-programming solver is the non-stochastic optimizer
  oracle used by unit tests.
