# Derivation Trace

1. Partial tracing a normalized two-qubit pure state gives two Schmidt eigenvalues `(1 +/- sqrt(1-C^2))/2`, proving `E(psi)=mathcal E(C)`.
2. The spin-flipped density is `S rho* S`, with `S=sigma_y tensor sigma_y`. The non-negative spectrum of `sqrt(sqrt(rho) tilde(rho) sqrt(rho))` equals the square roots of the spectrum of `rho tilde(rho)`.
3. For every HJW isometry, subnormalized ensemble columns reconstruct `rho` exactly. The triangle inequality applied to the tilde inner products gives average concurrence at least `lambda1-lambda2-lambda3-lambda4`.
4. A Takagi factorization turns the symmetric tilde-overlap matrix into subnormalized states whose diagonal overlaps are the concurrence eigenvalues. Real pair rotations equalize the signed preconcurrence when the leading eigenvalue dominates; a four-phase polygon construction cancels it when it does not. Both branches reconstruct the original density matrix and attain the analytic convex roof.
5. Reconstructing the HJW isometry from every generated ensemble verifies the converse direction independently of the forward ensemble generator. Bell/product endpoints, the Werner family, local-unitary invariance, random decompositions, and separable mixtures supply limiting and falsification checks.
6. For a pure state with Schmidt probability `p`, exact binomial type weights give a typical-subspace mass approaching one and a base-two dimension rate approaching `H2(p)`.
7. For `n` copies, let `M_n(D)` be the sum of the largest `D` product Schmidt probabilities. Keeping those coefficients constructs a rank-`D` approximation with squared fidelity `M_n(D)`. Conversely, transmitting `q` qubits from an initially product Alice/Bob cut creates Schmidt rank at most `2^q`, and the Ky Fan bound limits every such approximation to fidelity `M_n(2^q)`. Therefore the first `q` with `M_n(2^q)>=1-epsilon` is both achievable and necessary; asymptotic equipartition gives `q/n -> H2(p)` for vanishing `epsilon`.
8. The finite-dimensional convex hull lives in a 15-dimensional affine density-matrix space, so Caratheodory gives at most `15+1=16` pure states. Rank-one/rank-two formula checks and the spread of every constructed optimal component are recorded separately from historical attributions.

Use this file for formula-heavy papers. Every implemented equation should map
back to a source equation or an explicit derivation step.

## Formula Lane Rule

Every formula used by numerical code must have:

- a card in `EQUATION_CARDS.json`;
- a human-readable derivation in this file;
- a formula gate result in `outputs/checks/formula_verification.json`;
- a code pointer, or a note that it is not used in code.

Do not open a numerical target until its formula dependencies are traceable and
the formula gate is not closed.

## Equation Cards

### EQ001

- Source:
- Latex:
- Role:
- Derived from:
- Steps:
- Symbols:
- Numerical form:
- Code pointer:
- Status:
- Open questions:
