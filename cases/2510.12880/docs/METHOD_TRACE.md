# Method Trace

## METHOD001 — Exact conserved-sector construction

- Source: main Eqs. `eq.H`, `eq.Ws`; supplement spin-matrix convention.
- Role: replace a full \(3^N\) diagonalization by an algebraically exact block
  labeled by all \(w_j=\pm1\).
- Inputs: even \(N\), \(\theta\), and a requested \(w\) string.
- Outputs: ordered Cartesian product basis and the Hamiltonian matrix in that
  block.
- Algorithm:
  1. transform the local spin matrices to the Cartesian zero-state basis;
  2. enumerate base-three product configurations;
  3. retain only configurations satisfying every diagonal \(W_j=w_j\)
     constraint;
  4. apply each two-site X/Y bond operator and retain matrix elements inside
     the same sector;
  5. check Hermiticity and absence of transitions outside the block.
- Parameters: paper-exact \(K=\cos\theta\), \(Q=\sin\theta\), periodic even
  chains.
- Code pointer: `src/kitaev_aklt.py`.
- Checks: full-space versus assembled-sector spectra for \(N=4\); all basis
  states have requested \(w\); dimensions sum to \(3^N\).
- Status: verified. This is an exact change of basis and symmetry
  decomposition, not a solver approximation.
- Open questions: none.

## METHOD002 — Physical fractionalized MPS

- Source: main Fig. 3 and Eq. `eq.A_matrices`; supplement explicit \(B\), \(M\),
  and \(C\) matrices.
- Role: construct the uniform-\(+\) and one-flip ansätze used in main Fig. 5.
- Inputs: bond types, \(w\) string, and Cartesian sector configurations.
- Outputs: a normalized complex vector in the same basis as METHOD001.
- Algorithm:
  1. build \(B_X^\chi,B_Y^\chi,M^s,A_w^\chi\);
  2. contract \(C_{\lambda,w}^s=\sum_\chi(M^sB_\lambda^\chi)\otimes A_w^\chi\);
  3. transform the physical leg from \(m_z\) to \(x,y,z\);
  4. evaluate periodic traces for sector configurations;
  5. normalize and verify sector support.
- Parameters: bond dimension four; alternating X/Y tensors; no truncation.
- Code pointer: `src/kitaev_aklt.py`.
- Checks: selected printed \(C\) matrices, transfer-matrix norm, exact
  zero-energy expectation at \(\theta=\pi/4\), and uniform-\(-\) product-state
  identity.
- Status: verified.
- Open questions: the supplement contains two obvious \(M^{+1}\) versus \(M^0\)
  typos, resolved from its own definitions and resulting matrices.

## METHOD003 — Fixed-sector eigensolver and overlap extraction

- Source: main text states “exact diagonalization” for
  \(N=4,6,8,10,12\), but does not disclose solver or tolerances.
- Role: reproduce Fig. 5 without degeneracy-dependent eigenvector choices.
- Inputs: Hermitian fixed-sector matrix and matching normalized MPS vector.
- Outputs: lowest energy, residual norm, spectral gap within the sector, and
  squared overlap/fidelity.
- Algorithm:
  1. use dense Hermitian diagonalization when the exact block is small;
  2. otherwise use a sparse Hermitian solver with deterministic initial vector;
  3. require \(\|Hv-Ev\|<10^{-10}\);
  4. fix no arbitrary phase because the reported observable is a squared
     absolute overlap;
  5. for the first-excited manifold, solve one matching one-flip sector and
     separately confirm equality of all one-flip sector energies.
- Paper parameters: \(N=4,6,8,10,12\) and
  \(\theta=40^\circ,30^\circ,20^\circ,10^\circ,0^\circ\).
- Code pointer: `src/kitaev_aklt.py`,
  `scripts/run_paper_target.py`.
- Checks: residual, normalization, solver agreement on small \(N\), energy
  ordering, and the \(\theta\to45^\circ\) exact limit.
- Status: verified_reconstructed. The algebra and observable are exact; the
  solver protocol is reconstructed because the paper does not report it.
- Open questions: raw author overlap values are unavailable.

## METHOD004 — Source-panel digitization for comparison only

- Source: `internal-paper-reference/Overlap_GS_MPS_shrunk.png` and
  `Overlap_FE_MPS_shrunk.png`.
- Role: obtain approximate reference coordinates for numerical-closeness
  checks without treating pixels as generated scientific evidence.
- Inputs: known axes \(N=4,\ldots,12\), overlap range \(0.8\) to \(1.0\), and
  colored marker pixels.
- Outputs: digitized reference CSV with pixel uncertainty.
- Algorithm: calibrate the plot rectangle from axis lines, isolate the five
  marker colors near each known \(N\), and map median marker centers to data
  coordinates.
- Code pointer: `scripts/digitize_overlap_panels.py`.
- Checks: recovered x positions, monotone curve order, and manual overlay.
- Status: reconstructed.
- Open questions: antialiasing limits reference precision to roughly
  \(10^{-3}\); this does not affect independent-data coverage.
