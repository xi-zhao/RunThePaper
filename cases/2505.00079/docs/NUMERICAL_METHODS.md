# Numerical methods

## NUM001: independent NumPy correctness baseline

- Targets: T001-T005 diagnostic/anchor runs.
- State and boundary: integer link tensor `(4,L,L,L,L)`, periodic four-torus.
- Solver: exact coloured single-link Metropolis.
- Seeds: explicit CLI values; current evidence uses 5602-5604.
- Outputs: raw per-measurement CSV plus JSON run/summary records.
- Main numerical risk: critical slowing down and phase-sector metastability.
- Validation: nine focused unit tests and formula gate.

## NUM002: finite-torus analytic reference

- Target: analytic component of T005.
- Parameters: L=16, n=1,...,7.
- Solver: direct double-precision evaluation of
  `[n^-4+(L-n)^-4]/[(n+1)^-4+(L-n-1)^-4]`.
- Output: `outputs/data/idx56_analytic_paper_exact.csv`.
- This is deterministic and paper-exact as an analytic curve; it is not MC data.

## NUM003: planned GPU batching

The baseline is memory-light and action-correct but performs many global NumPy
operations. The A100 path should batch independent chains and preserve the same
local action and observable definitions. CPU/GPU cross-checks on fixed short
chains and ensemble moments are required before accepting speed claims.

## Performance evidence

| Target | Local run | Runtime | Result |
| --- | --- | ---: | --- |
| Z7, three beta points | each 200 measurements, skip 2, burn-in 500 | 42.8 s total cold | Polyakov feature recovered |
| Z4 | paper 10,000 measurements, skip 1, burn-in 2,000 | 46.95 s | ring recovered after symmetry augmentation |
| Z3 | 200 measurements, skip 2, burn-in 1,000 | 50.57 s | chi_S=4.731, failed target |

At the measured Z3 rate, the paper's 4,001,000 sweeps for one beta/size are
roughly 40 hours locally. Fig. 5's 640,000,000 sweeps per theory are not a
reasonable NumPy execution target.
