# Lessons Learned

## Case summary

- Paper: *Topological Phase Transition in Non-Hermitian Quasicrystals*
- PaperID: `1905.09460`
- Result: 21/21 numerical axes generated; score 84.29
- Main gaps: unreported laser transient controls and edge-state classifier

## What worked

- Reading the TeX and supplement as one derivation exposed three source
  inconsistencies before coding.
- The Fourier-dual spectrum test verifies the non-Hermitian Hamiltonian more
  strongly than checking only one rendered plot.
- A scaled determinant circle avoids overflow in products of 610 eigenvalue
  differences and preserves the quantized winding.
- Separating generation and pixel comparison makes the no-source-pixel rule
  mechanically auditable.
- Full paper scale was cheap enough locally: 106 dense eigensystems plus 51
  laser states completed in about 71 seconds.

## Pitfalls and reusable fixes

| Pitfall | Evidence here | Future rule |
| --- | --- | --- |
| A phase convention is easy to drop | `theta=0` moved the localized laser peak to `n=2`; Eq. S-31 requires `theta=phi+pi/2` | trace every implementation parameter back to the exact source equation, including derived phases |
| Paper prose can contradict equations/captions | PT identity sign, broken/unbroken label, and golden-ratio denominator conflict | maintain a source-inconsistency ledger before opening the numerical gate |
| A plotted observable may be undefined | laser “bandwidth” and edge-state count have no estimator | mark the method reconstructed and cap evidence instead of fitting source pixels |
| Numerically unstable direct evaluation can mimic source artifacts | source winding points scatter near `h_c`; stable evaluation is quantized | prefer a derived stable form and document why its pixels may differ |
| High SSIM is not complete evidence | reconstructed Fig. 3 has the best SSIM but missing transient metadata | apply scientific and parameter gates before pixel scoring |

## Recommended harness improvements

| Priority | Improvement | Reason |
| --- | --- | --- |
| P1 | Add a structured source-inconsistency ledger and gate | prevents silent choices between conflicting equations, prose, and captions |
| P1 | Require explicit estimator/classifier provenance for plotted derived observables | catches undefined bandwidth, edge-count, clustering, and threshold rules |
| P2 | Record equation-derived parameter transformations separately from printed literals | would have caught `theta=phi+pi/2` before the first full run |
| P2 | Report pixel-contract failures independently from scientific status | lighter annotation density should remain visible without invalidating correct physics |

## New Failure Modes

| Failure mode | Where it appeared | Detection |
| --- | --- | --- |
| derived-phase omission | first laser run used `theta=0` | assert the low-depth mode is centred at `n=0` under Eq. S-31 |
| undefined plotted estimator | Fig. 3 bandwidth | require an estimator field and evidence cap when absent from the source |
| undefined state classifier | Fig. S1(d) edge counts | require a classifier contract and test every source-stated landmark |
| stable result differs from source numerical artifact | Fig. 1(d) winding near `h_c` | compare direct and stable formulations and retain the derivation-backed result |

## Reusable Checks Or Tools

| Candidate | Reuse value | Suggested destination |
| --- | --- | --- |
| source-inconsistency ledger checker | forces an explicit resolution when prose, equations, and captions disagree | `private validation harness/rr_harness/` |
| derived-parameter trace | protects transformations such as `theta=phi+pi/2` | formula-card schema |
| estimator/classifier provenance gate | prevents source pixels from silently defining an omitted numerical method | target-contract checker |
| generation/reference import-boundary scan | mechanically verifies that numerical entrypoints cannot read source figures | provenance checker |

## Workflow change

For future cases: freeze source → map every numerical subpanel → build formula
cards → create a source-inconsistency ledger → trace every derived parameter →
run scientific assertions → only then open original figures for pixel scoring.
