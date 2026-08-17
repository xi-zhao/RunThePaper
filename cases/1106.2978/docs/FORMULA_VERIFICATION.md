# Formula Verification

All nine numerical formula cards are open and verified. The machine-readable result is `outputs/checks/formula_verification.json`.

| Formula | Role | Independent check | Status |
| --- | --- | --- | --- |
| EQ001 | boundary-driven XXZ Liouvillian | direct full-space stationary solve for `n=2,3,4` | passed |
| EQ002 | exact MPO amplitudes | finite auxiliary path plus root-of-unity closure | passed |
| EQ003 | transfer/vertex contractions | one- and two-point symmetry/bounds checks | passed |
| EQ004 | conserved current | dense bond currents and MPO ratio agree | passed |
| EQ005 | `Delta=1/2` reduced transfer | generic amplitudes reproduce printed `3x3` closure | passed |
| EQ006 | easy-plane thermodynamic current | finite `n=400`, limiting coefficients and maximum | passed |
| EQ007 | easy-axis insulating exponent | three independent coupling fits | passed |
| EQ008 | isotropic cosine and `n^-2` current | finite-size convergence through `n=400` | passed |
| EQ009 | correlation and weak-coupling limits | exact finite contractions at declared probes | passed |

No author numerical data, digitized source curve or source-image pixel enters any formula check.
