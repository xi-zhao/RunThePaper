# Method Trace

Use this file for algorithmic or systems papers where the key reproduction
object is a method rather than a formula.

## Method cards

| Method | Inputs | Steps | Outputs | Gate |
| --- | --- | --- | --- | --- |
| MTH001: analytic spectrum evaluation | 2×2 Hamiltonian coefficients and momentum grids | evaluate radicand → unwrap phase for continuous sheets → cross-check unordered eigenvalue pairs with `numpy.linalg.eigvals` → export arrays before rendering | EP/Dirac/hybrid spectra and invariant checks | verified for T002/T003/T006 |
| MTH002: domain-wall matching | two half-space parameter sets and conserved `k_y` | solve common-spinor sum/difference equations algebraically → choose the localized branch → verify both characteristic polynomials and spinor residual → cross-check representative points with nonlinear roots | bulk/edge complex energies | verified for T001/T004; residuals, Hermitian limit, localization, zero plane, and independent-root checks pass |
| MTH003: cylinder diagonalization | Supp. Eq. (13), `n=40`, 241 sampled `k_y` values | assemble block-tridiagonal `2n×2n` matrix → verify Bloch transform → dense eigensystem → identify edge weights from eigenvectors | real/imaginary band arrays and edge labels | verified: Fourier identity, Hermitian limit, eigenpair residual, analytic edge dispersion, and localization checks pass |

The original PDF/vector figures are never read by these methods. They enter
only after generated data and rendered artifacts exist.
