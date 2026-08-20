# Consistency report

## Supported evidence

| Evidence family | Independent result | Paper comparator | Verdict |
|---|---:|---:|---|
| Table I exact, N=3/N=4 | max abs gap `3.315e-4` | printed 4 decimals | supported |
| Table I WKB | max abs gap `9.612e-5` | printed 4 decimals | supported |
| Table II Eq. (11) | max abs gap `9.075e-5` | printed 4 decimals | supported |
| N=2 massless anchor | max gap `1.166e-3` | \(E_n=2n+1\) | supported |
| N=1 massive anchors | max gap `3.429e-4` | shifted oscillator | supported |
| Complex-WKB domain | all turning-point identities/half-planes pass | Eqs. (4)–(5) | supported |
| Contour deformation | three admissible bends agree at N=3,4 | isospectrality claim | supported |
| Hermitian limit | N=512 max square-well gap `4.315%` | width-two limit | supported |
| Near-one scaling | fitted exponent `0.652492` | printed `2/3` | supported |
| Near-N=2 merger | 192/256 quadrature agreement; high levels merge first | printed perturbative mechanism | supported |
| Massive phase anchors | exact N=0,1,2 and pair-count checks pass | massive-case discussion | supported |
| Fig. 1 scientific pixels | `97.4703/100` | predeclared scientific region | high fidelity |
| Fig. 3 scientific pixels | `86.7857/100` | predeclared scientific region | accepted |

## Stable discrepancy: Table II exact column

| \(\epsilon\) | Paper exact | Riccati shooting | Independent FD | shooting − paper |
|---:|---:|---:|---:|---:|
| `1e-5` | 4.7798 | 4.7795789222 | 4.7795658352 | -0.0002210778 |
| `1e-6` | 5.3383 | 5.3351639686 | 5.3351476621 | -0.0031360314 |
| `1e-7` | 5.8943 | 5.8558550636 | 5.8558368611 | -0.0384449364 |

- Direct cause: the last three printed values do not satisfy the independently
  solved paper eigenproblem at their stated precision.
- Root cause leading hypothesis: a publication-side numerical value or
  undocumented generation-path discrepancy.
- Code-error adjudication: no defect found after a full parameter audit,
  domain/grid convergence, two genuinely different solvers, analytic limits
  and exact earlier table anchors.
- Affected scope: only 3/7 exact entries of Table II. The other exact entries,
  all 7/7 asymptotic entries and 28 other targets are unaffected.
- Remaining action: refreshed protocol-v2 review of the 29-target package.
  Until then this remains a candidate discrepancy, not a confirmed erratum.
