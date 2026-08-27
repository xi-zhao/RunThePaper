# Numerical Methods

## Observable

For one frozen panel target, evaluate four integer-valued sequences versus the
paper's complete `M` grid: `N_analytic`, `N_min`, `g_analytic`, and `g_min`.

## Independent Implementation

- Formulas: `src/trotter_bounds.py` implements the ten verified equation cards.
- Search: monotone lower-bound binary search with a doubling bracket.
- Overflow control: the search compares `log(epsilon_hat)` with
  `log(epsilon)`; reported threshold values are exponentiated only near the
  accepted boundary.
- Provenance: no author-code module, source PNG, digitised point, or sampled
  source pixel is imported into generated data.
- Target isolation: `scripts/run_target.py --target <id>` must match both
  `PRAGENT_GUARDED_TARGET_ID` and the final-reproduction stage.

## Paper Parameter Sets

| Figure | Model | Method panels | `M` grid | `t` | `lambda` | `epsilon` |
| --- | --- | --- | --- | ---: | ---: | ---: |
| Fig. 2 | XX chain | det1, ran1, det2, ran2 | 7, 9, 11, 13, 15, 17, 19 | 2 | 7.071 | 1e-3 |
| Fig. 3 | TFIM | det1, ran1, det2, ran2 | 5, 8, 12, 15, 19 | 5 | 8.0 | 1e-5 |

## Acceptance Checks Per Row

1. `epsilon_hat(N_analytic) <= epsilon`;
2. `epsilon_hat(N_min) <= epsilon`;
3. `epsilon_hat(N_min-1) > epsilon` when `N_min>1`;
4. `N_analytic >= N_min`;
5. `g = M*N` for first order and `g = 2*M*N` for second order.

## Numerical Risk

The largest direct exponent during naive bracketing can overflow (for example,
`t*lambda*M=760` at `N=1`).  Log-domain predicate evaluation removes this
implementation risk without changing the threshold.  Integer values remain
well inside Python's arbitrary-precision range.  No stochastic seed, solver
tolerance, grid interpolation, or remote compute is involved.
