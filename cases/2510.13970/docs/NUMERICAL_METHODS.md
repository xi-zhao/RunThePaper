# Numerical methods

- Python/NumPy/SciPy dense complex linear algebra.
- Adaptive reference: `solve_ivp(method="DOP853", rtol=2e-12, atol=2e-14)` on the full unitary.
- Explicit check: midpoint product `prod exp[-i H(t_mid) dt]` at 64, 128, and 256 steps.
- Principal log: complex Schur decomposition, principal phases, Hermitian symmetrization.
- Norm: spectral/operator 2-norm.

At `omega=40`, the explicit midpoint Hamiltonian errors versus the adaptive reference are `1.3846e-5`, `3.4601e-6`, and `8.6493e-7`, demonstrating the expected factor-four second-order convergence.
