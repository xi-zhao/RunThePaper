# Formula Verification

Machine-readable result: `outputs/checks/formula_verification.json`.

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| EQ001 | problem-to-coloring objective | open | source traced; exact limiting-case enumeration passed |
| EQ002 | coordinates/controls-to-Hamiltonian | open | source traced; Hermiticity and physical-unit checks passed |
| EQ003 | encoding feasibility interval | open | source traced; finite-tail counterexamples retained |
| EQ004 | annealing controls and propagation | open | source traced; continuity and norm checks passed |

All formulas that feed the executed targets use `source_and_symbolic`; none is
opened by transcription alone.

## Closed Or Unclear Formulas

| Formula/target | Reason | Numerical consequence |
| --- | --- | --- |
| Figure 7 protocol-c | Appendix A.2 and caption disagree on Omega | T004 remains `missing_source_input`; no arbitrary parameter choice |

Run:

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/2504.08598 --write
```
