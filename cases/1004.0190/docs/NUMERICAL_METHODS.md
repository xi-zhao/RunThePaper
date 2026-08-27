# Numerical Methods

All matrices are generated independently with NumPy/SciPy. The closed two-qubit discord formula is tested against direct projective dephasing minimization. Classical-quantum states are independently constructed from random orthonormal bases and conditional density matrices. Haar unitaries and phase-times-involution controls test both sides of the DQC1 criterion. The multipartite channel uses a generalized Gell-Mann basis and an explicit subsystem permutation, then applies the same operator-Schmidt theorem to each party. The campaign covers 2–8 qubits and local dimensions 2–5; acceptance uses exact commutator, rank, basis-orthonormality, and search-manifold identities rather than noisy runtime monotonicity. A second generic channel minimizes the Hilbert--Schmidt distance after simultaneous local projective dephasing. It uses exactly `d(d-1)` complex-Givens coordinates per measured subsystem, not a redundant full-unitary parameterization, and validates the optimizer on rotated classical states, GHZ states, and maximally entangled qudits. The paper does not specify a unique multipartite measure convention, so this simultaneous-dephasing extension is declared reconstructed. The 3D renderer reads only frozen CSV output.

## Method Cards

### NUM001 — multipartite operator-basis campaign

- Target: T007
- Equations/method cards: EQ002, EQ008, NUM005
- Parameters: 2–8 parties; local dimensions 2–5
- Grid or benchmark: classical cat mixtures, GHZ states, and maximally entangled qudits
- Boundary conditions: finite Hilbert spaces, exact subsystem factorization
- Solver: direct singular-value decomposition of the right-operator coefficient map
- Tolerance: `1e-12` Schmidt-value and commutator threshold
- Random seed: none for T007
- Output schema: one row per state, party, and local dimension in `multipartite_scaling.csv`
- Validation checks: orthonormal basis, exact classical commutation, noncommuting GHZ/qudit operators, rank witness, analytic optimization dimension
- Numerical risks: runtime varies by host and is therefore recorded only as a diagnostic

### NUM002 — multipartite projective-distance optimizer

- Target: T007
- Equation cards: EQ003, EQ008, EQ009
- Parameters: 2–4 qubits, local dimensions 2–3, six deterministic multistarts
- Objective: squared Hilbert--Schmidt norm removed by local projective dephasing
- Coordinates: complex Givens rotations on `U(d)/U(1)^d`
- Output: `multipartite_discord.csv`
- Validation: rotated classical states give zero; GHZ gives `1/2`; maximally entangled qudits give `1-1/d`
- Scientific boundary: reconstructed simultaneous-dephasing convention because the publication does not print one unique multipartite objective

### NUM008 — zero-discord hardness boundary

- Target: T009
- Exact calculation: `Tr(e^{i phi}A)/d=e^{i phi}(N_+-N_-)/d` for `A^2=I`
- Validation: direct diagonal-matrix traces through eight register qubits
- Boundary: the runner records that the paper omits a succinct instance family, approximation tolerance, classical model, and hardness reduction; it does not turn the algebraic identity into a fake complexity proof

### NUM009 — regrouped DQC1 bipartition negativity

- Target: T010
- Observable: `N=(||rho^{T_A}||_1-1)/2`
- Enumeration: all `2^n-1` unique bipartitions with the control fixed on side A
- Smoke grid: three independent Haar unitaries for each `n=2,...,6`, `alpha=0.7`
- Validation: exact partition count, Hermitian partial transpose, Bell-state `N=1/2`, and zero negativity for the analytically separable control-versus-register split
- Boundary: negativity, the finite-size grid, Haar ensemble, and diagnostic threshold are independent proxy choices because the publication specifies none of them

## Efficiency And Reuse Plan

- Baseline implementation:
- Main bottleneck:
- Efficient implementation choice:
- Complexity or scaling:
- Performance bottleneck removed:
- Optional harness promotion candidate:
- Case-specific parts that should not enter the harness:
- Performance evidence:
