# Method Trace

- NUM001: Hermitian eigensolvers, the magic basis, and a complex-symmetric `tau` spectrum independently check the pure and mixed formulas.
- NUM002: A real-symmetric anti-linear Takagi eigensystem, signed preconcurrences, real rotations, and the inverse HJW map construct optimal positive-branch ensembles without a matrix-square-root branch choice.
- NUM003: An analytic collinear boundary plus lambda-polygon closure and the printed four sign rows construct zero-concurrence ensembles; 456 Bell-diagonal adversarial cases, random isometries, product mixtures, and Werner states independently try to falsify both branches.

Use this file for algorithmic or systems papers where the key reproduction
object is a method rather than a formula.

## Method Cards

### METHOD001 — constructive optimal ensemble

- Source: Eqs. (11)–(20)
- Role: prove attainability of the closed-form convex roof
- Inputs: an arbitrary 4x4 two-qubit density matrix
- Outputs: subnormalized state columns whose outer products sum to `rho`
- Algorithm: eigenensemble → Takagi basis → positive real rotations or zero-branch polygon → HJW converse
- Code: `src/wootters/model.py::optimal_decomposition`
- Checks: reconstruction, tilde orthogonality, phase closure, average concurrence, average entanglement, HJW isometry, exact degeneracies, zero modes, and separability-boundary states
- Status: implemented and exercised on ranks 1–4 plus the complete denominator-12 Bell simplex
- Open question: the paper's private random sample is unavailable; our campaign is explicitly independent
