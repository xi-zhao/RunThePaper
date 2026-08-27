# Derivation trace

1. Vectorize the tilted Lindblad operator `W_s`, multiplying only the counted jump recycling term by `exp(-s)`.
2. Obtain the scaled cumulant generating function `theta(s)` as the eigenvalue with largest real part. Differentiate it for activity `k=-theta'` and Mandel parameter `Q=-theta''/theta'-1`.
3. For the two-level special point `kappa=4 Omega`, derive the printed closed form `theta=-2 Omega(1-exp(-s/3))`; use it as an independent check of the generic superoperator.
4. Recover rate functions through the convex dual `phi(k)=sup_s[-s k-theta(s)]` and check the two-level analytic expression.
5. Generate representative event records from the actual clean-room quantum-jump process (or a model-derived postselection window), with fixed seeds and measured activities.
6. For the micromaser diagonal sector, reduce the tilted Lindblad equation to a birth-death generator over photon number. Use a symmetric tridiagonal similarity transform for stable dominant eigenvalues and a direct nonsymmetric eigenvector check for `rho_s(N)`.
7. Verify the printed generalized Doob transform using the dominant left eigenmatrix, including trace preservation, the two-level rate-rescaling identity, and the explicit three-level mapped Hamiltonian/jump realization.
8. Freeze numerical CSV/JSON and hashes before original-figure rendering or layout optimization.
