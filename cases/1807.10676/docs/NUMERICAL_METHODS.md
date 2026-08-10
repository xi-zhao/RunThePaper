# Numerical Methods

## NUM001 — continuum eigenproblem

- Targets: T001, T005-T009
- Equations: EQ001-EQ003 and EQ005
- Basis: complete hexagonal reciprocal shells; adaptive cutoffs `4,6,7,10,11,12`
- Solver: sparse Hermitian shift-invert eigenpairs near zero; dense diagonalization only for small matrices/local vorticity work
- Convergence: each reported magic alpha is recomputed at cutoff `N+1`; maximum velocity delta `0.00147356 < 0.01`
- Risk controlled: incomplete rectangular truncations can break C3 and create false splittings

## NUM002 — Wilson spectra

- Targets: T002, T004, T010, T011
- Equation: EQ004
- Grid: continuum `25 x 81`; lattice models `61 x 101`
- Method: occupied frames, SVD polar-unitary neighbor overlaps, reciprocal embedding, determinant phase removal, eigenphase continuity
- Validation: C2x spectral symmetry and expected odd/trivial winding pattern
- Risk controlled: a wider Ritz window prevents selecting the wrong central subspace near close levels

## NUM003 — node position and vorticity

- Target: T008
- Inputs: independently computed MBM central gap
- Method: minima on a `29 x 29` hexagonal BZ grid followed by Nelder-Mead refinement; duplicates removed with torus distance
- Vorticity: sign of the local two-band Jacobian in a `C2T=K` real gauge
- Acceptance: maximum retained gap residual below `3e-7`

## NUM004 — lattice Hamiltonians

- Targets: T003, T004, T011, T012(c)
- Equations: EQ006, EQ007, EQ009
- Solver: dense Hermitian eigensystems on Gamma-K-M-Gamma paths
- Analytic gate: TB4 Gamma levels agree to `2.22e-16`; intervalley `zeta` opens the intended gap

## NUM005 — projected Wannier density

- Target: T012(b)
- Equation: EQ008
- Grid: `15 x 15` reciprocal points, real-space radius 4 cells
- Method: lower-four-band projector, `S^{-1/2}` Löwdin frame, discrete Fourier transform
- Gate: `15.821507 <= det S(k) <= 16.000000`

## NUM006 — rendering and pixel evidence

- Rendering consumes frozen NPZ files only.
- Source panels become readable only after `generated_data_manifest.json` exists.
- Allowed changes: canvas, axes, fonts, line/marker style, palette, interpolation.
- Forbidden changes: parameters, arrays, cutoffs, grids, source pixels/vectors as data.
- Primary metric: foreground point-wise RGB similarity inside predeclared scientific regions; full canvas is layout diagnostics only.

## Performance

The full 12-target local CPU run takes about 98 seconds. Sparse central eigensolvers and adaptive complete shells make the campaign practical; GPU transfer and remote-session overhead would dominate this workload. The deferred VASP work is CPU/RAM/license-bound and is not made feasible by the available A100 alone.
