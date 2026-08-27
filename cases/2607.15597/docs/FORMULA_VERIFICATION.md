# Formula Verification

Machine-readable gate: `outputs/checks/formula_verification.json`.

The gate passed with 13/13 numerical cards open. “Open” means the formula is
traceable and may feed code; it does not promote reconstructed formulas to
paper-exact evidence.

| Formula | Role | Gate | Evidence |
| --- | --- | --- | --- |
| EQC001 | Branch forces | verified/open | Taylor expansion + source equation |
| EQC002 | Displacement/geometric phase | verified/open | Magnus solution and closure limit |
| EQC003 | CZ condition | verified/open | Direct substitution gives pi |
| EQC004 | Spin observables | verified/open | Coherent-state Gram matrix; normalization test |
| EQC005 | Rydberg decay | verified/open | Survival law and limiting cases |
| EQC006 | Thermal feature model | reconstructed/open | eta-squared limit and disclosed checkpoints |
| EQC007 | Chain duration | reconstructed/open | Source plateau/crossover/endpoint only |
| EQC008 | Interconnect time | reconstructed/open | Hybrid/photon exact; QCCD curve inferred |
| EQC009 | Memory amortization | verified/open | Negative derivative; source figure conflicts |
| EQC010 | Fowler projection | source-only/closed | Direct substitution misses Table S11 by roughly 2–8×; retained for review, not execution |
| EQC011 | Multi-mode closure | verified/open | Exact piecewise integral |
| EQC012 | CZ distance | verified/open | Algebra and dimensions |
| EQC013 | Circular error floors | source-only/open | Disclosed lifetime and additive budget |

## Disclosures that cap claims

- EQC006 does not reproduce the five-order Taylor-Hamiltonian QuTiP run.
- EQC007 cannot reproduce the exact Fig. 3 curve without optimized schedules.
- EQC008's QCCD fit is visual/prose reconstruction.
- EQC010 does not reproduce the Monte Carlo data points used to calibrate it.
- EQC013 treats circular C4 values as paper inputs because SM S9 quotes an
  uncertainty range inconsistent with the value adopted by its own table.

No implemented target depends on a closed formula gate.
