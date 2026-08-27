# Method Trace

The paper is formula-led rather than algorithm-led. These method cards describe
how the verified formulas are evaluated without changing their physical
meaning.

## METHOD001 — Sparse Fock-basis Wigner evaluation

- Source: End Matter descriptions of Figs. 1 and 2; standard Fock-basis matrix
  element cited there.
- Role: evaluate pure and reduced states containing Fock coherences.
- Inputs: sparse collective-mode amplitudes or a finite density matrix,
  complex phase-space coordinates.
- Outputs: real Wigner values in the paper's \(2/\pi\) convention.
- Algorithm steps:
  1. evaluate associated Laguerre polynomials for every nonzero density-matrix
     element;
  2. sum \(W_{|m\rangle\langle n|}\rho_{mn}\);
  3. multiply independent collective-mode factors;
  4. discard residual imaginary roundoff only after checking Hermiticity.
- Parameters: maximum Fock number 4; no Hilbert-space truncation error because
  the printed state has finite support.
- Code pointer: `src/wigner_gme.py`.
- Checks: vacuum normalization, diagonal Fock formulas, Hermitian reality, and
  comparison with explicit displaced-parity matrices through \(n=4\).
- Status: `verified`.
- Open questions: none.

## METHOD002 — Deterministic polar quadrature

- Source: finite-disk definition in the main text and the Fig. 1 slice
  definition in the End Matter.
- Role: integrate absolute and negative Wigner volumes.
- Inputs: analytic Wigner functions, radial cutoff, radial and angular orders.
- Outputs: signed integral, negative volume, absolute volume, and convergence
  diagnostics.
- Algorithm steps:
  1. map Gauss--Legendre nodes to the finite radial interval;
  2. use a uniform periodic angular rule;
  3. include the polar Jacobian;
  4. repeat at increasing resolutions;
  5. compare against analytic integrals where available.
- Parameters: Fig. 1 final grid \(640\times2048\), radial cutoff 4 in the
  collective coordinate; Fig. 2 uses its exact antiderivative.
- Code pointer: `src/wigner_gme.py:polar_negative_volume`.
- Checks: exact W-state disk formula, exact illustrative-state signed
  integral, and convergence envelope below \(5\times10^{-6}\).
- Status: `verified`.
- Open questions: the source does not disclose its Fig. 1 integration grid.

## METHOD003 — Finite characteristic-matrix eigensolve

- Source: finite-point characteristic corollary and the Fig. 2 End Matter.
- Role: reproduce the seven-point W-state GME witness.
- Inputs: \(\Xi\), analytic W-state characteristic function, vacuum filter.
- Outputs: 7-by-7 Hermitian matrix, sorted eigenvalues, minimum-eigenvalue
  witness, and 19 unique pairwise differences.
- Algorithm steps:
  1. enumerate \(\Xi\) exactly from \(\xi_0\);
  2. form all pairwise differences;
  3. evaluate the analytic matrix entry for each difference;
  4. verify Hermiticity;
  5. use a Hermitian eigensolver.
- Parameters: \(N=7\), \(\xi_0=(85+147i)/200\), vacuum filter.
- Code pointer: `src/wigner_gme.py:characteristic_witness_matrix`.
- Checks: 19 unique differences, trace one, six positive eigenvalues, and
  \(\mathcal N_C=0.017580375648\ldots\).
- Status: `verified`.
- Open questions: none.

## METHOD004 — Source-to-reproduction visual comparison

- Source: rendered `Overview.pdf` and `Wstate.pdf`.
- Role: compare scientific topology and panel content without treating copied
  source pixels as numerical evidence.
- Inputs: original panel render and independently generated PNG.
- Outputs: side-by-side comparison images.
- Algorithm steps: preserve source aspect ratio, place source and generated
  panels side by side, and annotate the generated evidence separately.
- Parameters: rendering-only; not used for numeric acceptance.
- Code pointer: `scripts/run_paper_target.py`.
- Checks: source asset availability and generated-artifact existence.
- Status: `reconstructed`.
- Open questions: Fig. 1 isosurface levels and camera are not reported.
