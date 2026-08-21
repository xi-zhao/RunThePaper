# Method Trace

- NUM001: normalized Pauli-basis Bloch and operator-Schmidt analysis.
- NUM002: direct optimization over projective measurement directions.
- NUM003: formula-generated Bell-diagonal geometry and constrained extrema.
- NUM004: direct DQC1 block-matrix trace and commutator checks.
- NUM005: generalized Gell-Mann bases, subsystem permutation, and operator-Schmidt commutators for every party; exact projective-basis manifold dimensions expose scaling without timing-based acceptance.
- NUM006: minimal complex-Givens coordinates span each local projective-basis manifold; deterministic multistart minimization evaluates the reconstructed multipartite Hilbert--Schmidt dephasing distance.

Use this file for algorithmic or systems papers where the key reproduction
object is a method rather than a formula.

## Method Cards

### METHOD001 — subsystem-versus-rest discord criterion

- Source: final sentence before acknowledgements, built from Eqs. (5)–(7)
- Role: make the claimed arbitrary-subsystem extension executable
- Inputs: a density matrix, subsystem dimensions, and a measured subsystem
- Outputs: Schmidt rank, pair count, maximum commutator norm, and rank witness
- Algorithm steps: permute the selected subsystem left; expand in an orthonormal Hermitian basis; directly SVD the right-operator coefficient map; apply the declared tolerance to singular values; test all retained left-operator commutators
- Parameters: 2–8 qubits and local dimensions 2–5 in the frozen campaign
- Code pointer: `src/geometric_discord/model.py::multipartite_discord_criterion`
- Checks: fully classical cat mixtures commute for every party; GHZ and maximally entangled qudits are detected; bases are orthonormal; search dimensions equal `sum_j(d_j^2-d_j)`
- Status: implemented
- Open questions: the paper does not specify one unique multipartite objective; the implemented simultaneous-local-dephasing convention is explicit and reconstructed

### METHOD002 — multipartite geometric-discord optimization

- Source: bipartite geometric distance definition plus the final multipartite-extension statement
- Role: make the progressively difficult measure evaluation executable
- Inputs: density matrix, local dimensions, measured subsystem set
- Output: minimized Hilbert--Schmidt dephasing distance and optimizer diagnostics
- Algorithm: parameterize each local projective basis with complex Givens rotations; dephase in the product basis; minimize the removed off-block norm over deterministic multistarts
- Code pointer: `src/geometric_discord/model.py::multipartite_geometric_discord`
- Checks: rotated classical states, GHZ analytic value, maximally entangled qudit analytic value, unitary-coordinate orthonormality
- Status: implemented as an explicitly reconstructed convention
