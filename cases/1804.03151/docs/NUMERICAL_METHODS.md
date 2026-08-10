# Numerical Methods

## NUM001 — potentials and continuum bands

- Targets: T001-T003, T008-T010
- Equations: EQ001, EQ002, EQ006, EQ008, EQ009
- Basis: complete hexagonal plane-wave shells, cutoff 5 (91 states)
- Convergence: cutoff 6 (127 states); maximum path differences 0.000987 meV main and 0.000183 meV supplement
- Solver: `numpy.linalg.eigh/eigvalsh`
- Grids: 61 points per symmetry-path segment; 41x41 DOS k grid; 151x151 contour grid
- Output: compressed NPZ arrays with units in field names

## NUM002 — tight-binding and period sweeps

- Targets: T002, T005-T007, T010-T012
- Equations: EQ003, EQ005, EQ007, EQ009
- Fit: ordinary linear least squares on a 15x15 momentum grid
- Period grids: 28 points over 5.5-19 nm; 16 points over 7-8.5 nm
- Interaction: 5x5 Bloch grid, 81x81 real-space grid, FFT image-charge convolution
- Determinism: no random numbers or fitted source pixels
- Numerical risk: interaction sweeps use a declared finite Bloch/real grid and are treated as reduced-resolution scientific targets

## NUM003 — Wannier display

- Target: T004
- Equation: EQ004
- Gauge: phase chosen positive at the potential maximum
- Grids: 9x9 Bloch momenta and 121x121 real-space points
- Validation: integral of probability density equals one to numerical precision

## Efficiency and reuse

- Baseline complexity is repeated diagonalization of 91x91 Hermitian matrices.
- Basis vectors and Fourier links are precomputed once per moire period.
- Tight-binding extraction is a single linear solve rather than nonlinear fitting.
- Coulomb projection uses FFT convolution instead of a four-dimensional real-space integral.
- The full 12-target CPU run is about 30 seconds on the local Apple M4; transfer to A100 would add overhead and offers little value at these matrix sizes.
- The physics module stays case-local; complete-shell enumeration and run isolation are reusable harness patterns.
