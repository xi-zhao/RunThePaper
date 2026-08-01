# Formula Verification

Six formula objects feed the numerical reproduction:

| ID | Object | Independent checks |
| --- | --- | --- |
| EQ001 | effective nonreciprocal coupling | symmetry and hyperbolic limits |
| EQ002 | steady-state battery energies | exact energy identity, author arrays, and S3 normalization limit |
| EQ003 | coupling derivatives | symbolic differentiation and finite differences |
| EQ004 | forward transmission | two-channel reduction and optimum coupling |
| EQ005 | affine Gaussian dynamics | two independent Gaussian solvers and finite-Fock probe |
| EQ006 | passive energy and ergotropy | symplectic invariant, vacuum limit, positivity |

All gates pass. The main-text transmission equation contains a brace typo, so
the unambiguous supplemental scattering matrix is used. This source correction
is documented rather than silently patched.

Figure S3 contains a second source correction. Its axis says
`E_i^ss/omega_b`, but all curves visibly start at one. EQ002 gives unequal
absolute baselines and exactly unit normalized baselines, so the generated
observable is `E_i^ss/E^ss`. Both arrays are public, and author confirmation is
still required to determine whether the paper error is limited to the label.

The Figure S1 discrepancy does not close EQ005: the exact moment closure is
verified. It rejects the source panel's implied convergence because a cutoff-10
probe peaks near 3.75 while the cutoff-free solution peaks near 59.97.
