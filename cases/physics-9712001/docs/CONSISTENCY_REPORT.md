# Consistency report

## Supported results

| Evidence | Independent result | Paper comparator | Verdict |
|---|---:|---:|---|
| Table I exact, all N=3/N=4 rows | max abs gap `3.315e-4` | printed 4 decimals | supported |
| Table I WKB, all rows | max abs gap `9.612e-5` | printed 4 decimals | supported |
| Table II Eq. (11), all rows | max abs gap `9.075e-5` | printed 4 decimals | supported |
| N=2 massless spectrum | max gap `1.166e-3` | \(E_n=2n+1\) | supported |
| N=1 massive spectrum | max gap `3.429e-4` | shifted oscillator | supported |
| Fig. 1 scientific pixels | `97.4703/100` | predeclared scientific region | high fidelity |
| Fig. 3 scientific pixels | `86.7857/100` | predeclared scientific region | accepted |

## Stable discrepancy: Table II exact column

| \(\epsilon\) | Paper exact | Riccati shooting | Independent FD | shooting − paper |
|---:|---:|---:|---:|---:|
| `1e-5` | 4.7798 | 4.7795789222 | 4.7795658352 | -0.0002210778 |
| `1e-6` | 5.3383 | 5.3351639686 | 5.3351476621 | -0.0031360314 |
| `1e-7` | 5.8943 | 5.8558550636 | 5.8558368611 | -0.0384449364 |

### Direct cause

The paper's last three printed exact values do not agree with the two independent calculations at their stated four-digit precision.

### Root-cause assessment

The leading hypothesis is a publication-side numerical discrepancy. It is only **probable**, not confirmed: protocol-v2 fresh review has not yet independently adjudicated the case.

### Code-fault assessment

No defect was found after four distinct checks:

1. the complete printed epsilon grid and Hamiltonian were audited;
2. two different numerical formulations agree within `1.83e-5`;
3. changing the shooting boundary changes results by only `1.59e-8`;
4. Eq. (11), the first four exact rows, N=2, and the massive N=1 limits all pass.

### Affected scope

Only 3/7 entries in Table II's exact column are affected. The other 4/7 exact entries, all 7/7 asymptotic entries, both plotted figures, Table I, and every analytic/convergence check pass.

### Next discriminating test

A fresh reviewer must rederive the N=1 patch equation and rerun both formulations at higher precision without seeing this report. Only that review can promote the issue to `paper_error_candidate`; otherwise it remains inconclusive or becomes a reproduction defect.
