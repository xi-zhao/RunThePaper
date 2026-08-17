# Numerical Methods

## Method Cards

### NUM001 — Zigzag-ribbon diagonalization

- Target: T001, Main Fig. 1 band axes.
- Equations/method cards: EQ001-EQ008; METHOD001-METHOD003.
- Parameters: `t=1`, `t2/t=0.03`; width 20 with widths 16/20/24 for
  convergence. Width is reconstructed because the paper does not print it.
- Grid or benchmark: 401 momenta over `0 <= k_x a <= 2 pi`.
- Boundary conditions: open zigzag boundaries, Bloch-periodic along the strip.
- Solver: dense Hermitian eigendecomposition independently at every momentum
  and spin; analytic continuum/scalar checks use direct formulas.
- Tolerance: Hermiticity `1e-12`, Kramers crossing `1e-10`, bulk-gap relative
  error 8%, two-largest-width feature difference 4%.
- Random seed: not applicable; the calculation is deterministic.
- Output schema: full per-state CSV with energy, spin, band index and edge
  weights; width convergence CSV; analytic/science JSON.
- Validation checks: edge coordination, Hermiticity, time reversal,
  particle-hole symmetry, Kramers crossing, edge localization, bulk-gap and
  width convergence, spin Chern pair, transport and material-scale estimates.
- Numerical risks: choosing the wrong honeycomb termination produces a
  bearded edge and moves the flat band to the wrong momentum interval.

## Efficiency And Reuse Plan

- Baseline implementation: build and diagonalize the complete Bloch matrix.
- Main bottleneck: repeated eigendecomposition over momentum and widths.
- Efficient implementation choice: exploit conserved spin, diagonalize one
  `2W x 2W` block per spin, and reuse the immutable geometric neighbour graph.
- Complexity or scaling: `O(N_k W^3)` time and `O(W^2)` working memory.
- Performance bottleneck removed: geometry is built once per width, not once
  per momentum.
- Optional harness promotion candidate: numerical/render process separation
  with frozen-data hash verification.
- Case-specific parts that should not enter the harness: honeycomb neighbour
  orientation and zigzag termination rules.
- Performance evidence: formal numerics took 0.554 s; complete sandboxed run
  including setup and attestation took 1.086 s.
