# Formula Verification

All eight formula/method cards pass their declared gates.

- The phase-free Clifford quotient contains exactly 720 two-qubit actions.
- The Bell-reference test gives `S(R)=1`; measuring its system partner gives `S(R)=0`.
- A random Clifford/measurement circuit preserves a full-rank commuting tableau.
- T001 independently locates the finite-size crossing at `p=0.16` versus `0.1598(5)`.
- T002 puts 98.97% of purification-event weight inside the microscopic causal cone.
- All two-reference mutual informations are nonnegative.
- One- and four-reference critical entropies both decay.
- Mixed-stabilizer conditioning passes the Bell-pair dephasing/projection distinction, packed-rank parity, and full-record/pure-trajectory equivalence checks.

`check_formula_gate.py` provides the machine-readable gate result. T003 is now formula-valid and method-equivalent at reduced scale. Its old out-of-window-measurement omission is recorded as a resolved reproduction defect, not a paper defect.
