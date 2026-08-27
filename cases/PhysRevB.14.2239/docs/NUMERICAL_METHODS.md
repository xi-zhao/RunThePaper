# Numerical Methods

| Target | Numerical object | Paper-scale settings | Solver/check |
| --- | --- | --- | --- |
| T001 | rational spectrum | every reduced p/q, q<50 | Hermitian eigensolver + transfer trace |
| T002 | skeleton | pure cases through N=37 and central special cases | exact band intervals |
| T003 | L2 cell | rational sampling q<=79 | exact map + affine energy transform |
| T004 | C2 cell | rational sampling q<=79 | exact map + affine energy transform |
| T005 | smeared quadrant | delta-alpha=0.01, q<=79, 480x480 | interval raster + alpha-only dilation |
| T006 | three wavefunctions | 1/5, 2/11, 17/93 | periodic eigensolver + modular reorder |
| T007 | supporting checks | all above | 11 independent invariants; no separate denominator item |
| T008 | irrational Cantor-spectrum theorem | not yet implemented | nested-cell/rational-approximant topology and measure test required |
| T009 | spectrum/measure continuity theorem | not yet implemented | separate set-valued and Lebesgue-measure convergence tests required |

The implementation uses dense Hermitian diagonalization for q<=93. Cached band
edges are reused across figures, so the completed display campaign takes under
one second of scientific-runtime time on the local Apple Silicon CPU and peaks
below 80 MiB RSS. T008-T009 require new analytic/numerical evidence design, not
an A100 or a larger rerun of the existing display campaign.

## Parameter boundary

The paper-exact inputs are Fig. 1's `q<50`, Fig. 2's `N<=37`, Fig. 5's
`delta-alpha=1/100`, and every Fig. 6 fraction/eigenvalue. The paper does not
print Figs. 3–5 sampling density, rational cutoff or raster resolution; q<=79
and 480x480 are reproducible convergence/render settings, not inferred paper
parameters. The physical model and coordinate transformations remain exact.

## Data boundary

Only generated `.npz`/`.json` data feed the renderer. Author code, author arrays,
digitized curves and source pixels do not enter the numerical process.
