# Formula Verification

Machine-readable gate: `outputs/checks/formula_verification.json`, generated with
`python PRAgent-workflow/scripts/check_formula_gate.py case/1804.03151 --write`.

| Formula | Role | Gate | Evidence |
| --- | --- | --- | --- |
| EQ001 | moire potential | verified | Real, periodic and C3-closed first shell. |
| EQ002 | continuum spectrum | verified | Hermitian; cutoff delta below 0.001 meV. |
| EQ003 | tight-binding fit | verified | Complete neighbor shells and small declared fit residual. |
| EQ004 | Wannier transform | verified | Unit normalization from Bloch eigenvectors. |
| EQ005 | screened interactions | verified | Direct FFT projection; U0>U1>U2. |
| EQ006 | DOS/density | verified | Units close and 2-degree density equals 2.5529e12 cm^-2. |
| EQ007 | exchange | verified | Printed expressions recover J2/J1≈0.060 near 3 degrees. |
| EQ008 | Fermi contour | verified | Filling quantile lies on computed band and shows expected nesting. |
| EQ009 | mismatch system | verified | Aligned period and bandwidth match reported scales. |

No implemented formula remains closed or unclear. The DFT blocker is a method/input
problem and does not feed any formula-derived target.
