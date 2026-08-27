# Method Trace

## MTH001 — Deterministic Closed-Form Evaluation

- Source: the seven verified equation cards and the paper's visible axis/order
  declarations.
- Role: convert the complete analytic model into structured data and both
  numerical figures.
- Inputs: occupation or `epsilon/T` grids and Rényi orders
  `1/4,1/2,1,2,4`.
- Outputs: three CSV files, two PNG/PDF/SVG figure families, and a scientific
  validation JSON.
- Algorithm:
  1. evaluate the Fermi-Dirac logistic function;
  2. evaluate P/W/Q bodies;
  3. apply the determinant and entropy maps;
  4. insert exact analytic bounds/crossings;
  5. render on author-matched canvases;
  6. run source-isolated scientific assertions;
  7. only then compare with source figures.
- Randomness: none.
- Solver/tolerance: no iterative solver; floating-point checks use `1e-14`.
- Code: `scripts/run_reproduction.py` and
  `src/fermionic_phase_space.py`.
- Status: verified.
- Open questions: none affecting any numerical figure.

## Provenance Boundary

The generation method has no path to `paper-source/*.pdf` or
`internal-paper-reference/*.png`. `scripts/build_pixel_comparisons.py` is a
separate terminal evaluator and records `source_pixels_used_in_generation=false`.
