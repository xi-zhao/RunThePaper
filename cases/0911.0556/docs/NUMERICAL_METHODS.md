# Numerical methods

- Two-/three-level systems: dense complex tilted Liouvillian diagonalization (`4x4` and `9x9`) with central finite-difference and left/right eigenvector checks.
- Rate functions: grid-based Legendre-Fenchel transform, independently anchored by the exact two-level formula.
- Event records: fixed-seed Monte Carlo wave-function propagation. Fig. 1 uses the exact Doob-equivalent two-level rate rescaling; Fig. 2 selects finite windows from a long physical blinking trajectory using generated counts only.
- Micromaser: photon-number birth-death generator with `N_ex=100`, `nu=0.15`, cutoff convergence and stable tridiagonal largest-eigenvalue evaluation.
- Renderer: separate post-freeze process; no scientific array can be altered after hashing.

The implementation never reads or translates author code. Source figures are not digitized and never provide numerical values.
