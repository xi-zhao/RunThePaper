# Numerical methods and evidence boundary

## Independent computation

The runner constructs the cavity mesh, boundary matrices, scattering solutions,
resonance state, near field, and far field from the equations. It cannot use
paper images as numerical input. No author source code or author-generated
numerical data were consulted. Paper images enter only after the generated NPZ
is frozen, for layout and styling diagnostics.

## Mesh and quadrature

The geometry uses two coupled rounded hexagons with declared circular corner
fillets. The feature configuration contains 432 constant boundary elements and
Gaussian quadrature for nonsingular interactions. Analytic diagonal limits
handle the logarithmic Green-function singularity. The paper-scale 1600-element
mesh is not claimed because the exact element placement is unavailable.

## Three linked calculations

1. A coarse-plus-fine scan evaluates the plane-wave scattering cross section.
2. An SVD at the reported complex resonance obtains the boundary null state.
3. That one state reconstructs both the near-field intensity and far-field
   angular distribution.

The run checks linear-system residuals, an optical-theorem consistency metric,
singular-value convergence at the resonance, interior/exterior field contrast,
and inversion of the far-field pattern. The frozen generated-data SHA-256 is
recorded in the public scorecard evidence.

## RenderContract

The second render pass may change only canvas size, axes placement, fonts,
grayscale, line width, palette, and interpolation. It reads the same frozen
arrays and does not alter the mesh, refractive index, resonance, scan values,
or field samples. Foreground pixel similarity is the main visual diagnostic;
full-image SSIM is secondary because background pixels dominate sparse plots.
