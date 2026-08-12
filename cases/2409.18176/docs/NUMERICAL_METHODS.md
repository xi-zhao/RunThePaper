# Numerical methods

## Formula-derived production path

1. Solve the ideal-gas chemical-equilibrium constraints for every detuning and
   temperature.
2. Build radial `l=1` collision operators from Supplement Eqs. (17)--(19).
   The angular delta function is integrated analytically; no artificial
   linewidth is needed in the Boltzmann lane.
3. Solve the complex sparse linear system for holes, excitons, and trions.
4. Integrate velocity-weighted departures to obtain the three conductivities.
5. Evaluate the Kubo self-energy on an independent quadrature grid.
6. Solve the printed three-fluid equations directly as a complex `3x3`
   system and compare with their closed form.
7. Write CSV/NPZ numerical arrays before rendering any plot.

## Execution profiles

- `smoke`: small radial grids for unit and conservation checks.
- `feature`: locally affordable detuning/temperature/frequency grids used for
  the first isolated run.
- `paper_scale`: code-complete convergence campaign with radial-grid doubling,
  cutoff expansion, and both analytic-delta and narrow-Gaussian parity.  It is
  checkpointed by parameter point and may run on CPU workers; the A100 is not
  intrinsically advantageous for the sparse solves.

## Scientific checks

- chemical-equilibrium residual and both density-conservation residuals;
- detailed balance of each collision kernel;
- nonnegative dissipative quadratic form at `Omega=0`;
- exact zero-coupling recovery of Drude holes and zero drag;
- resonance maximum near `Delta_star`;
- exciton-drag sign change across `Delta_star`;
- high- and low-detuning return toward background transport;
- Kubo/Boltzmann agreement through leading order in `g^2`;
- direct `3x3` and printed closed-form three-fluid parity;
- radial-grid/cutoff convergence and checkpoint-resume identity.

## Source boundary

The scientific runner receives only `src`, its entrypoint, and a
frozen configuration.  It cannot read `raw/`, `references/`, the Zenodo
record, source figures, or author arrays.  RenderContract optimization occurs
only after CSV/NPZ hashes are frozen and may change presentation parameters
only.
