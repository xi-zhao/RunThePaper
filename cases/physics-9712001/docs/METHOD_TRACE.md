# Method Trace

| Method | Paper source | Independent implementation role | Cross-check |
| --- | --- | --- | --- |
| Schrödinger eigenproblem | Eq. (2), paragraphs below Fig. 2 | sparse finite difference on real/complex contours | `N=2` harmonic oscillator and resolution convergence |
| Runge-Kutta patching | numerical-method paragraph on p. 3 | Riccati log-derivative shooting, not author code | finite-difference ground state away from the singular limit |
| complex WKB | Eqs. (4)-(5) | direct gamma-function evaluation | Table I and exact `N=2` limit |
| near-one asymptotics | Eqs. (6)-(11) | log-domain scalar solve | Table II trend and independent exact shooting |
| massive shifted oscillator | Eq. (1) at `N=1` | analytic completion of the square | all three Fig. 3 families |

The method description in the paper is used as scientific knowledge. No author
implementation, matrix, sample points or numerical output is reused.
