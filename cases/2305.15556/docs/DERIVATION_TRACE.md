# Derivation Trace

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

### EQ001 - pure-state QFIM

- Source: main covariance equation after Eq. (3); Supplement Eqs. (S34),
  (S43).
- Role: turns a state and a normalized Hermitian operator basis into the
  observable used by every target.
- Steps:
  1. For a unitary coordinate, `partial_mu |psi> = -i G_mu |psi>`.
  2. Insert this derivative into four times the real quantum geometric tensor.
  3. The result is four times the centered real Gram matrix of the vectors
     `G_mu|psi>`.
  4. A Gram matrix is positive semidefinite; a materially negative eigenvalue
     therefore diagnoses an implementation or precision error.
- Numerical form: apply each sparse generator once, subtract expectation-value
  products, take `4*real`, and symmetrize.
- Code pointer: `src/optimal_generators/model.py::qfim`.
- Status: verified.

### EQ002 - Rayleigh-Ritz optimal generator

- Source: Main Eq. (3) and the geometric conclusion of Supplement Sec. IV.
- Role: identifies maximal sensitivity and its generator.
- Steps:
  1. A normalized coefficient vector `o` defines `G(o)=sum_mu o_mu G_mu`.
  2. Its QFI is the quadratic form `o^T F o`.
  3. Rayleigh-Ritz gives `max_{o^T o=1} o^T F o=lambda_max(F)`.
  4. If `lambda_max` is simple, the eigenvector is unique up to sign. If it is
     repeated, only the leading eigenspace projector is unique.
- Numerical form: symmetric eigendecomposition, descending eigenvalues,
  residual checks, sign tracking only outside degenerate clusters.
- Code pointer: `model.py::qfim_eigensystem` and
  `model.py::tracked_optimal_generator`.
- Status: verified.
- Open question: Fig. 2(b) does not publish an eigenvector gauge for its
  degenerate intervals, so coefficient-pixel equality is not invariant.

### EQ003 - fixed-N boson representation

- Source: Main Eq. (9); Supplement Sec. I and Eq. (S44).
- Role: supplies exact finite-dimensional SU(2) and SU(4) matrices.
- Steps:
  1. Enumerate all occupation tuples `(n_1,...,n_k)` with sum `N`.
  2. Apply `a_i^dagger a_j` using the exact square-root occupation amplitude.
  3. Form x/y components from raising and lowering matrices and form the three
     printed Cartan combinations.
  4. Verify the 15-operator trace Gram matrix is diagonal with equal entries.
  5. For four modes the dimension is `binom(N+3,3)`; at N=20 this is 1771.
- Numerical form: CSR sparse matrices and complex128 states.
- Code pointer: `src/optimal_generators/bosons.py` and
  `model.py::su4_operator_basis`.
- Status: verified.

### EQ004 - one-axis twisting

- Source: Main Eqs. (6)-(7) and Fig. 1(a-b) caption.
- Role: generates both Husimi-Q surfaces and the SU(2) state used by T003/T004.
- Steps:
  1. The x-polarized coherent state has binomial amplitudes in the Jz basis.
  2. `Jz^2` is diagonal, so each occupation component receives the exact phase
     `exp(-i tau m^2)` with `tau=chi t`.
  3. The Husimi value is the squared overlap with another coherent state.
  4. At `tau=0`, the distribution peaks at the positive x direction and the
     QFIM spectrum is `(N,N,0)`.
- Numerical form: analytic phase evolution and direct coherent-state overlap.
- Code pointer: `model.py::oat_state`, `model.py::husimi_q`.
- Status: verified.

### EQ005 - analytic OAT comparator

- Source: Main Eq. (8) and the following optimal-axis paragraph.
- Role: an independent closed-form check on T003/T004.
- Steps:
  1. Evaluate the printed `A(tau)` and `B(tau)` moments.
  2. Diagonalizing the covariance block in the y-z plane produces the square
     root in `F_OAT` and the half-angle `delta`.
  3. At zero time the result is exactly the SQL, `F=N`.
  4. The paper limits agreement with the maximum eigenvalue to the initial
     squeezing regime; after the branch exchange it follows a lower branch.
- Numerical form: closed float64 expression with `atan2(B,A)/2`.
- Code pointer: `model.py::oat_analytic_qfi` and
  `model.py::oat_analytic_axis`.
- Status: verified.

### EQ006 - SU(4) three-axis twisting

- Source: Main Eq. (10), its explicit initial ket, and Supplement Eqs.
  (S12)-(S18).
- Role: generates T005/T006.
- Steps:
  1. Build `R=Q^+ + Sigma^+ = u^dagger d + s^dagger c`.
  2. The dimensionless Hamiltonian is `R R^dagger`, equivalently the printed
     `(Q^+ + Sigma^+)(Q^- + Sigma^-)`; it is Hermitian.
  3. Acting with the printed `J_y` rotation on the all-u state yields the
     coherent state `(u^dagger+c^dagger)^N/sqrt(2^N N!)`.
  4. Propagate from `tau=0` to `pi/2` in the 1771-dimensional symmetric basis.
  5. Evaluate the 15-dimensional QFIM at every stored time.
- Numerical form: sparse `expm_multiply`, exact printed operator basis, and
  independent dense parity at smaller N.
- Code pointer: `model.py::su4_hamiltonian`,
  `model.py::su4_initial_state`, `model.py::evolve_su4`.
- Status: verified.
- Open question: the adjacent prose says the explicit ket is an eigenstate of
  `J_x` and `K_y`. Direct variance checks give `J_x` and `K_z`; this potential
  axis-label error is retained for falsification.

### EQ007 - multiparameter anchors

- Source: main multiparameter paragraph after Fig. 2.
- Role: checks the SU(4) result without using any source curve.
- Steps:
  1. Include `tau=pi/4` exactly in the time grid.
  2. Sort the 15 QFIM eigenvalues descending.
  3. Compare indices 1, 3, and 8 against `0.307 N^2`, `0.189 N^2`, and
     `0.117 N^2` at the printed three-decimal precision.
  4. Check the associated reported generator subspaces commute, allowing for
     rotations within degenerate eigenspaces.
- Numerical form: numeric assertions only; these printed values never feed the
  generator.
- Code pointer: `src/optimal_generators/reproduction.py::science_checks`.
- Status: source-only quantitative cross-check with an open numeric gate.
