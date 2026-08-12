# Formula Verification

All nine executable formula cards have a source or standard derivation, code
pointer and independent check.  The same-n Stark matrix is checked against its
exact analytic spectrum, the second-order correction against \(F^2\) scaling,
the line shape against its Gaussian limit, and the metrology claims with exact
decimal or quadrature arithmetic.

EQ005 is deliberately an approximation: it only resolves small hyperfine
branch separations.  EQ003/T009 omit higher-order QED and finite-size terms.
These boundaries keep the targets at feature/partial level even though the
formula gate is open for executing the declared model.

Machine-readable result: `outputs/checks/formula_verification.json`.
