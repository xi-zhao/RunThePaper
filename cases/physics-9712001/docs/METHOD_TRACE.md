# Method Trace

| Method | Paper source | Independent implementation role | Cross-check |
| --- | --- | --- | --- |
| Schrödinger eigenproblem | Eq. (2), paragraphs below Fig. 2 | sparse finite difference on real/complex contours | `N=2` harmonic oscillator and resolution convergence |
| Runge-Kutta patching | numerical-method paragraph on p. 3 | Riccati log-derivative shooting, not author code | finite-difference ground state away from the singular limit |
| complex WKB | Eqs. (4)-(5) | direct gamma-function evaluation | Table I and exact `N=2` limit |
| near-one asymptotics | Eqs. (6)-(11) | log-domain scalar solve | Table II trend and independent exact shooting |
| massive shifted oscillator | Eq. (1) at `N=1` | analytic completion of the square | all three Fig. 3 families |
| opening oscillator examples | opening paragraph | analytic completion of the square | four exact sequences |
| Airy obstruction | Eqs. (6)-(7) | independent complex Airy evaluation plus Wronskian identity | five real-energy probes |
| classical transition | Eq. (12) and following text | log-gamma period and analytic angles | `N=2,3,4` periods and an `N=1.5` geometry case |
| Hermitian comparison | paragraph following Table I | real-axis sparse eigensolver for `p^2+|x|^N` | paired grids and the width-two square-well spectrum through `N=512` |
| near-one scaling | Eq. (11) and Table II caption | log-domain root sequence and independent slope fit | `epsilon=10^-40..10^-200` approaches exponent `2/3` |
| contour-deformation invariance | text following Eq. (3) | repeat the spectrum on three admissible smooth contours | N=3 and N=4 low levels remain invariant within declared tolerance |
| near-N=2 merger perturbation | behavior-near-N=2 paragraph | complex-symmetric two-level reduction with Gauss-Hermite quadrature | 192/256-order agreement and high-level-first merger ordering |
| massive exact anchors | Eq. (1), massive-case paragraph | analytic spectra at N=0,1,2 | independent sign and normalization checks for all three masses |

The method description in the paper is used as scientific knowledge. No author
implementation, matrix, sample points or numerical output is reused.
