# Method trace

## MTH_EXACT — analytic ground-state lane

Evaluate the four affine energy densities in Eqs. (2a)–(2d) and select all
degenerate minima. This is deterministic, parameter-complete, and sufficient
for Fig. 2.

## MTH_MC_SOURCE — historical Monte Carlo lane

- square periodic lattice, single-spin Metropolis kinetics;
- 400 MCS per spin for ordinary phase-boundary points;
- up to millions of kept MCS for small-lattice cumulants;
- each cumulant point repeated at least once and averaged.

Status: **reconstructed but not paper-exact**. RNG, seeds, burn-in, temperature
grid/history, exact kept-count allocation for most figures, and raw data are
missing. A 16-color parallel update can preserve noninteracting-site updates on
GPU, but it is an implementation-equivalent reduced run, not the historical
single-site trajectory.

## Historical source-curve lane — excluded from the public method

An earlier audit considered extracting comparison coordinates from publisher
figures. That lane is not part of this public reproduction. Numerical inputs
must come from equations, declared parameters, or independent simulation; any
post-freeze visual assessment must compare rendered rasters without turning
paper pixels into scientific data.
