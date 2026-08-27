# Derivation Trace

## Scientific chain

The paper starts from the constrained PXP Hamiltonian, whose basis contains no
adjacent up spins.  In that basis each permitted spin flip has unit matrix
element.  The deformation multiplies that matrix element by

\[
1-\sum_{d=2}^{R}h_d(z_{i-d}+z_{i+d}),
\]

which is exactly the numerical form used in `HamiltonianFamily`.

The printed ansatz

\[
h_d=h_0\left(\phi^{d-1}-\phi^{-(d-1)}\right)^{-2}
\]

is inserted into the SU(2) constraint (main Eq. 6).  Solving its scalar root
independently fixes `h0`; then \(h=2\sum_{d\ge2}h_d(-1)^d\),
\(\Delta=(1-h)^2\), and \(\tau=2\pi/\sqrt{2\Delta}\).  No printed decimal is
used as a numerical input.

Time evolution applies `exp(-iHt)` to the Néel basis vector.  The Loschmidt
echo is the squared Néel amplitude.  The half-chain coefficient matrix is
formed from the same state vector; its singular values give the reduced-density
probabilities and von Neumann entropy.

For the FSA, `H+` retains only transitions increasing Hamming distance from the
Néel state.  Recursion and normalization give \(|k\rangle\) and
\(\beta_{k+1}=\lVert H^+|k\rangle\rVert\).  A spin-\(N/2\) representation
predicts \(\beta_{k+1}\propto\sqrt{(N-k)(k+1)}\).  Applying
\(H^z=[H^+,H^-]\) to each FSA vector yields the mean, variance, and harmonic
spacing used for Main Fig. 3.

Symmetry-resolved spectra are built from translation orbits and bond-centred
inversion before diagonalization.  Adjacent-gap ratios and unfolded spacings
are then computed within a sector, avoiding false Poisson statistics caused by
mixing symmetries.

At paper scale the sector projection remains sparse until a memory preflight
authorizes the complete real dense block required for Main Fig. 2 and Supp.
Fig. S4.  Supp. Fig. S5 instead uses shift-invert around zero because its
observable depends on two exact interior scars, not the whole spectrum.

The supplement's intensive revival observable follows directly from the
many-body fidelity: \(\tilde g=g^{1/N}\) and
\(\Gamma=(1-\tilde g)/m\).  The ground-state Schmidt spectra, eigenstate
overlaps, and entropies all come from independently diagonalized Hamiltonians.

For N=60 the explicit constrained basis is not formed.  The same Pauli strings
are compiled into a finite-state MPO, and two-site DMRG targets the ground state
and a first excitation penalized by the generated ground-state projector.
Small-system tests compare this MPO and both DMRG eigenvalues against the
independent exact Hamiltonian.

For the toy model, expanding
\(V_{i-1,i+2}P_{i,i+1}\) produces a two-Pauli term minus three four-Pauli
terms, each with coefficient \(J/4\).  This is the Pauli-string construction
in `toy_hamiltonian`.  The fully polarized state has support only on the
embedded total-spin multiplet and therefore returns at integer periods.

For the perfect-revival lemma, write the initial state in the energy basis.
Unit-modulus return at a fixed time forces every occupied energy to have one
common phase, hence \(E_\mu=(\alpha+2\pi m)/\tau\).  Local bounded terms give
\(\lVert H\rVert\le Nh\), so the spectral width is at most \(2Nh\) and contains
at most \(K\le\lfloor 2Nh\tau/(2\pi)\rfloor+1=O(N)\) distinct compatible
energies.  Finally, \(\sum_\mu|c_\mu|^2=1\) implies
\(\max_\mu|c_\mu|^2\ge1/K=O(1/N)\).  The case-local checker constructs the
energy lattice and verifies the phase, count, and normalization steps without
using paper pixels or author arrays.

## Assumptions and execution boundaries

- Periodic boundary conditions are used for main-text targets; open boundaries
  are used for the low-energy supplementary target, matching the paper.
- The executed nine outputs remain explicitly exploratory `reduced_scale`
  results.  Paper-scale code readiness and smoke evidence do not replace them.
- The paper-scale Supp. Fig. S3 lane searches a local maximum around every
  revival and checkpoints the selected state through m=1000.  The earlier
  reduced run's analytic-period sampling remains disclosed only as historical
  evidence.
- The toy-model random realization is unavailable.  A new deterministic seed
  series is used; only distribution-level and exact-subspace features are
  compared.
- Supplement Fig. S2 omits N and R.  N=20,R=10 is a section-continuity
  inference, not an author-supplied datum.

## Code map

| Formula cards | Numerical implementation |
| --- | --- |
| EQ001-EQ004 | `src/scar_reproduction.py` Hamiltonian and coupling functions |
| EQ005 | reduced `run_main_figure_1`; paper scale `paper_scale.run_t001` and streamed `Bipartition` |
| EQ006 | `sector_hamiltonian_sparse`, `level_statistics`, `paper_scale.run_t002` |
| EQ007 | reduced `fsa_basis`; paper scale `_streaming_fsa` |
| EQ008 | reduced `run_supp_figure_s3`; paper scale `paper_scale.run_t006` |
| EQ009 | `toy_hamiltonian_sparse`, `paper_scale.run_t009` |
| EQ010 | `atomic_closure.perfect_revival_overlap_bound` and its analytic tests |
