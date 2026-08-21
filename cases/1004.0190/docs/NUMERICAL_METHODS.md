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

## Efficiency And Reuse Plan

- Baseline implementation:
- Main bottleneck:
- Efficient implementation choice:
- Complexity or scaling:
- Performance bottleneck removed:
- Optional harness promotion candidate:
- Case-specific parts that should not enter the harness:
- Performance evidence:
