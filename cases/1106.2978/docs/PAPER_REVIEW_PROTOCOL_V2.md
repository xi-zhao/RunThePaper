# Paper Review Protocol V2

## Review question

Can a fresh reviewer, without the original reproduction conversation, independently confirm or falsify the complete numerical inventory, exact MPO implementation, parameters, frozen results and paper-consistency verdict for T001-T006?

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
- Determine whether the 15.16% finite-size correlation residual is compatible with the printed leading-order statement.

This case currently emits no paper-error candidate. The independent reviewer result must not be fabricated by the reproducing context.
