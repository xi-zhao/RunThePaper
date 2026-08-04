# Method Trace

## MTH001 — Deterministic finite-width TRY evaluation

- Source: main numerical example; Supplement S2--S5.
- Role: convert the verified Fresnel and Fisher equations into reproducible
  structured target artifacts.
- Inputs: paper geometry, source window, noise floor, target ID.
- Outputs: one target-specific CSV, scientific check JSON, PNG, and comparison
  board.
- Algorithm:
  1. Build an odd-size uniform source grid over the complete paper window.
  2. Build Gauss--Legendre nodes independently on each physical slit.
  3. Evaluate \(E_0,M_t,M_f\) directly from the complex Fresnel kernel.
  4. Form scores, noise weight, full Fisher matrix, optimized codes, toy codes,
     coded Fisher matrices, and retention eigenvalues.
  5. For FIGS001, repeat steps 2--4 at the five printed slit widths.
  6. Serialize only the explicitly guarded target; plotting reads its generated
     arrays and never the source image.
- Parameters: all claim-relevant values are copied into each target's
  paper/generated mapping; numerical grid controls are case-owned and are
  checked for convergence.
- Checks: doubled quadrature order, refined source grid, score finite
  differences, Fisher positivity, code orthogonality, retention bounds,
  printed-value comparison, and deterministic rerun hashes.
- Status: `verified`.
- Open questions: none for the frozen scope.
