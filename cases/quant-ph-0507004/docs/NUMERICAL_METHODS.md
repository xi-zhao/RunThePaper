# Numerical methods

| Method | Purpose | Scale | Validation |
| --- | --- | --- | --- |
| symmetric tridiagonal eigensolver | exact parity spectra/eigenvectors | full band to N=5000 | independent dense N=18 matrix |
| value-window tridiagonal eigensolver | separatrix convergence | N up to 250000 | parity and full-band overlap checks |
| linear least squares | Fig. 1 coefficient and log-log exponents | 1080 finite-window gaps; 30 large-N gaps; 3x500 critical levels | selector/parity/convention sensitivity |
| separatrix action plus exact eigenvector mass profiles | super-scarring | direct two-lobe quadrature and 9 systems up to N=1440 | WKB-predicted indices; first-20 mass; 50/75/90/99% widths; pair-external neighbours |
| complete same-parity gap binning | normal-phase spacing versus energy | every adjacent gap at N=2000, both parities, 20 bins | exact pair-count conservation and lower/full-band trend split |
| explicit self-adjoint coordinate quantization | ordering sensitivity after Eq. (15) | two prescriptions, N=40..1280, four couplings, both parities | Hermiticity, full-spectrum comparison, fitted N exponent |
| certified characteristic double-root solve | exceptional points in complex lambda | N=10..30, both parities, deterministic multi-seed campaign | matrix-norm backward errors plus direct eigenvalue gap, center, and eigenvector-condition certificates |

The tridiagonal representation uses O(N) memory and O(N^2) full-spectrum time,
which makes the printed paper scale cheaper and more reliable than a dense
spin matrix. The exceptional-point campaign solves the algebraic double-root
conditions directly and certifies each retained root through a different
matrix observable; it never re-labels a sampled avoided crossing or failed
search as an exceptional point. Because local seeds are not a certified root
count over a continuous complex domain, absence and N-to-infinity statements
remain explicit evidence boundaries. There is no randomness and no GPU
requirement.
