# Numerical Methods

## NUM001 — exact ground-state map

- Target: T002 / Fig. 2
- Equations: EQ001-EQ002
- Parameters: dense `(R,R')` grid spanning the published panel
- Solver: vectorized evaluation of four affine energies and `argmin`
- Boundary conditions: periodic only for independent pattern checks
- Outputs: NPZ arrays, generated PNG, analytic audit JSON
- Validation: all four explicit patterns reproduce the printed energies; phase boundaries are pairwise energy equalities
- Risk: degeneracy pixels on exact boundaries; resolved by using energies rather than visual colors as truth

## NUM002 — exploratory A100 specific heat

- Targets: T009-T010 / Figs. 9-10
- Equations: EQ001 and the energy-fluctuation specific heat
- Parameters: `R=0`, `R'=0.8`; `L=24,36,48,60`; `T=0.6…2.0` at 29 points
- Sampling: eight replicas, 400 burn-in and 400 measured sweeps, seed `19850501`
- Boundary conditions: periodic square lattice
- Solver: Torch Metropolis in 16 independent color classes
- Output: one JSON containing settings, energy/specific-heat curves, SEMs, peaks, and a naive `1/L` fit
- Feature gates: peak temperature near 0.7, nondecreasing peak height, sensible thermodynamic-limit intercept
- Result: all three feature gates failed
- Numerical risk: severe metastability and autocorrelation in a first-order region; independent site-coloring does not solve equilibration

## Efficiency And Reuse Plan

The GPU coloring is interaction-safe because no equal-color sites share any NN, diagonal, or distance-two bond. It removes serial site-update overhead, but future correctness requires replica exchange or multicanonical weights, phase-specific starts, convergence traces, and effective-sample-size accounting. Those physics-specific parts remain case-local until validated.
