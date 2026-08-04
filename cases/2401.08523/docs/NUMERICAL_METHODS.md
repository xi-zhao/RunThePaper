# Numerical Methods

## NUM001 — Main Figure 1

- Target: T001.
- Equation: EQ001.
- Grid: 1,201 uniform values of `epsilon/T` on `[-6,6]`.
- Solver: stable vectorized logistic evaluation.
- Output: `outputs/data/figure_1_fermi_dirac.csv`.
- Checks: particle-hole symmetry, midpoint `n(0)=1/2`, and both limits.
- Numerical risk: ordinary `exp(x)` can overflow on much wider domains; the
  implementation uses a sign-split stable form.

## NUM002 — Main Figure 2(a-c)

- Target: T002.
- Equations: EQ002-EQ006; EQ007 supplies an application check.
- Grid: 2,001 occupation values on `[0,1]`.
- Orders: `r=1/4,1/2,1,2,4` exactly as plotted.
- Solver: direct vectorized algebra; no fitting, interpolation, or optimization.
- Outputs: `figure_2_moments.csv` and `figure_2_entropies.csv`.
- Checks: exact bounds, all three crossings, entropy limit, Rényi monotonicity,
  and the thermal-channel audit.
- Numerical risk: zero bodies produce real mathematical divergences. CSV files
  retain `inf`; Matplotlib breaks/clips only the visible line segment.

## Rendering And Pixel Evidence

- Rasterization: 180 dpi, matching the frozen author vector references.
- Canvas sizes: `933 x 625` and `2723 x 625` pixels.
- Renderer: Matplotlib/Agg; the author used Wolfram/cairo, so font rasterization
  remains an honest source of pixel difference.
- Source pixels are absent from generation and are introduced only by the
  Harness pixel-layout and comparison steps.

## Efficiency

- Complexity: `O(N)` time and memory in grid points.
- Full data/check/PNG/PDF/SVG run: about `0.55 s` on local Apple Silicon CPU
  after font-cache warmup.
- No GPU, external service, checkpoint, or large-scale run is needed.
