# Method Trace

## MTH001 — Self-consistent atomic–cavity fixed point

- Source: published Eq. (3), the dynamic potential before Eq. (1), and Supplement Eqs. (S1)–(S5).
- Role: generate the nonlinear photon number and self-consistent atomic densities.
- Inputs: AA Hamiltonian, pump `eta`, cavity wave vector `gamma_c`, `N`, `Delta_c`, `kappa`, `U`, and an initial field/state.
- Outputs: normalized ground-state orbital, complex steady cavity field, photon number, IPR and convergence residuals.
- Algorithm:
  1. form the effective diagonal potential from the current cavity field;
  2. solve its lowest tridiagonal eigenpair;
  3. recompute the cavity field from density overlaps `Theta` and `B`;
  4. damp state and field updates;
  5. continue the converged solution along a descending pump grid.
- Parameters: mixing `0.35`, tolerance `1e-10`, maximum 5000 iterations.
- Code: `src/ldsi_model.py::solve_self_consistent_state` and `continue_self_consistent_branch`.
- Checks: zero-pump limit, state normalization, branch convergence, source-scale onsets/endpoints, localized-peak sharpening.
- Status: `reconstructed`; the paper does not print the iteration scheme or S1 pump values.
- Open question: exact author initialization/branch-selection policy.
