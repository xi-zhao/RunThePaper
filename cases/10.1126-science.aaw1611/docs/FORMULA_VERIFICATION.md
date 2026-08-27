# Formula Verification

Machine-readable result: `outputs/checks/formula_verification.json`.

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| EQC001 | calibrated Bose-Hubbard Hamiltonian | open | main Eq. 1/S24/Table S1 traced; Hermiticity and units checked |
| EQC002 | fixed-number matrix elements | open | ladder algebra, dimensions, and number conservation checked |
| EQC003 | coherent evolution | open | no-decoherence source statement; unitarity and t=0 checked |
| EQC004 | density and entropy | open | reduced-state identity and normalization checked |
| EQC005 | correlation and concurrence | open | Eqs. S25-S27 traced; one-particle reduction checked |
| EQC006 | group velocity | open | Eqs. S28-S30 and 153.99 sites/us source traced |
| EQC007 | Gij and double occupancy | open | main Eq. 3; operator and pair-sum identities checked |
| EQC008 | hard-core comparator | open | paper limit traced; projected-Hamiltonian identity and zero double occupancy checked |

## Result

All 8 cards are open; 0 are blocked. Numerical implementation began only after
this gate passed. Re-run with:

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/10.1126-science.aaw1611 --write
```
