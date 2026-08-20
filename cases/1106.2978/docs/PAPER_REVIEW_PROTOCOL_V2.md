# Paper Review Protocol V2

## Review question

Can a fresh reviewer, without the original reproduction conversation,
independently confirm or falsify all 24 numerical publication items covered by
the 21 target contracts, the exact MPO implementation, parameters, frozen
results and two source discrepancies?

## Two-phase boundary

1. Phase 1 reads only the paper/inventory bundle and freezes every numerical figure, subfigure and quantitative text claim before seeing implementation evidence.
2. Phase 2 reads that immutable inventory and a narrative-free falsification bundle containing formulas, code, configuration, frozen data, tests and run attestation.
3. Each target must receive at least one explicit attempt to disprove it using a limit, invariant, alternative derivation or independent numerical method.
4. The reviewer may not read the original reproduction-session explanations.

## Paper-error threshold

A discrepancy is not a paper error merely because one run differs. Promotion requires a source pinpoint, two distinct strong checks, an explicit falsification attempt, and evidence excluding reproduction-code error, parameter ambiguity and compute ambiguity.

## Known falsification focus

- Re-inventory the entire Fig. 2(b) logarithmic axis and inset, because an earlier reproduction configuration missed the `n=100..400` domain.
- Recheck current normalization and dissipator convention with a direct Liouvillian construction.
- Test the isotropic `n^-2` coefficient and easy-axis exponent without fitting source pixels.
- Re-derive the correlation kernel and test its exact reflection-plus-spin-flip symmetry, including possible variable or sign transcriptions.
- Substitute `lambda=pi*l/m` into the complete Eq. (7) at both `r=m` and
  `r=m-1` for odd and even `m`.  Adjudicate the printed cutoff index, hopping
  parity and `H_(m+1)` dimension against the paper's own `m=3` three-state
  reduced matrix.  Do not reuse the superseded diagnostic that forced the
  singular same-index choice `tau_m=-cos(m*lambda)`.
- Verify the complete 25-item publication inventory (24 numerical items plus
  the schematic), including the boundary-divergence proof, general transfer-MPO
  formulas, easy-plane spectral convergence, infinite-rank construction and
  isotropic-current asymptote.  Every numerical item must map explicitly to a
  target; closely coupled statements may share a target only when the mapping
  is scientifically justified.

The reproducing context records two stable discrepancies but emits no paper-error candidate. Only a fresh-context reviewer may promote or reject them.
