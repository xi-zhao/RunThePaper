# Consistency Report

This report separates reproducible numerical evidence from claims about the
paper. A successful calculation can reveal a paper discrepancy; it is not then
relabelled as a failed artifact.

## Whole-Paper Summary

| Class | Targets | Meaning |
| --- | --- | --- |
| Paper-exact computation | T001, T002, T006, T007, T011, T014 | Printed parameters or exact equations are sufficient for the executed calculation. |
| Bounded paper subset | T003--T005, T008--T010, T012, T013, T015--T017 | Code and data are complete, but the paper omits a finite grid, threshold, tolerance, comparison point, or RG definition. |
| Stable source discrepancy awaiting fresh review | T002, T004, T006, T007, T014 | Independent derivation/implementation disagrees with a printed sign, shortcut, or offset. |
| Missing-source deferral | Higher-dimensional area-law statement | The paper supplies no model, region, discretization, or numerical coefficient, so no honest target can be constructed. |

All 17 executable targets pass their declared numerical assertions. This says
that the reproduction artifact is sound; it does not pre-accept every paper
claim. The isolated v6 run completed in 6.720 s from clean Git SHA `267a4bb2`,
with 459 recorded file events and zero forbidden accesses.

## Material Consistency Questions

| Target | Printed statement | Independent result | Current adjudication |
| --- | --- | --- | --- |
| T002/T014 | Eq. (3) has a ferromagnetic overall sign, while Fig. 2 describes the critical antiferromagnetic XXX curve. | Full-space diagonalization, fixed-sector Lanczos, and analytic ferromagnetic ground states retain the incompatibility. | Stable discrepancy; fresh review required. |
| T004 | Eq. (11) prints occupied probability `(1+nu)/2` under definitions that imply `(1-nu)/2`. | Direct fermion algebra and an independent Pauli/Fock representation agree; entropy and unordered spectrum are invariant to the label exchange. | Stable sign/label discrepancy; numerical entropy remains valid; fresh review required. |
| T006 | The printed XX `g0` shortcut is presented as the covariance coefficient. | The defining integral and an independent closed form agree with each other and not with the shortcut. | Stable discrepancy; fresh review required. |
| T007 | The printed critical-Ising coefficient shortcut and stated/depicted offset are mutually inconsistent. | Integral, FFT/closed-form checks, and independent long-L fits agree on the scaling slope but not all printed constants. | Stable discrepancy; fresh review required. |
| T003 | Eq. (21) is universal, but the publication does not disclose its finite numerical verification range/tolerance. | 32/32 declared Ising/XX finite tests pass. | Bounded support, not a universal proof. |
| T015 | Entanglement is said to decrease along RG flow without publishing a lattice RG map or observable matching rule. | A declared mass-flow proxy is monotonic. | Inconclusive proxy; it cannot self-prove the paper claim. |
| T010 | The paper invokes an unknown scaling function `f(x)` without publishing it, a grid, or tolerance. | A frozen fixed-coordinate proxy is internally consistent. | Reviewer-defined proxy, not reproduction of `f(x)`. |
| T017 | The number of relevant Schmidt states should grow only polynomially, without defining relevance. | Algebraic, resolved, and three retained-weight ranks are reported separately. | Epsilon-rank proxy, not an exact-rank or asymptotic proof. |

## Code-Error Adjudication

No current discrepancy is attributed to reproduction code. This conclusion is
based on focused unit tests, exact limits, covariance and spectrum invariants,
parameter/source audits, independent numerical paths, convergence checks, and
the isolated run attestation. It remains falsifiable: a fresh-context reviewer
must try to identify a code, method, parameter, or convention error before any
paper discrepancy may be promoted to `paper_error_candidate`.

## Presentation Evidence

Only the two actual numerical figures receive pixel comparisons. Their
predeclared scientific-region scores are 85.1606 (Fig. 1) and 98.0797 (Fig. 2).
The other 15 targets are equations or quantitative text claims, so their
evidence is numerical/analytic and `not_comparable` to a source panel. The
RenderContract changed no physical parameter or frozen array.
