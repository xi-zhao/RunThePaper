# Formula Verification

`outputs/checks/formula_verification.json` reports 9/9 cards open for numerical
use.  Every card has a source trace, independent derivation/sanity check and
code pointer.

| Cards | Role | Gate | Independent check |
| --- | --- | --- | --- |
| EQ001-EQ003 | PXP Hamiltonian, deformation, ansatz | verified | constrained connectivity, Hermiticity, monotone couplings |
| EQ004 | SU(2) constraint | verified | root h0=0.0506656 with near-zero residual; Delta and tau agree |
| EQ005 | fidelity and entropy | verified | g(0)=1, S(0)=0, Schmidt normalization |
| EQ006 | level statistics | verified | symmetry resolution and 0<=r<=1 |
| EQ007 | FSA algebra | verified | normalized recursion and spin-N/2 limiting form |
| EQ008 | intensive decay rate | verified | exact N-th-root definition and bounded fidelity |
| EQ009 | toy Hamiltonian | verified | Hermiticity and exact integer-period returns |

Open scientific limitations are parameter-scale questions, not closed formula
gates: T006 samples the analytic period rather than searching every local
maximum, and T009 uses a new disclosed random realization.
