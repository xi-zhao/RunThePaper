# Lessons Learned

Use this file after each reproduction pass. The goal is to extract reusable
lessons from one paper and turn them into better Agent and harness behavior for
the next paper.

## Case Summary

- Paper: Vidal et al., *Entanglement in quantum critical phenomena*
- PaperID: quant-ph-0211074
- Final status: review pending
- Main reproduced targets: Main Figs. 1--2 and Eq. (21) majorization claim
- Main blockers: fresh-context classification of the XXX sign inconsistency

## What Worked

- Fourier-covariance methods reproduce both XY critical slopes cheaply and
  provide the full entanglement spectrum needed for majorization checks.
- A fixed-magnetization sparse basis reduces the N=20 XXX problem to 184,756
  states; the complete campaign finishes on CPU in seconds.
- Preserving both sign conventions turns a confusing plot mismatch into a
  precise, falsifiable scientific-review question.

## What Was Difficult

- The XXX sign convention requires two independently labeled calculations and
  an analytic treatment of the degenerate ferromagnetic ground manifold.
- Pixel agreement alone would conceal the printed-equation/caption conflict.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Treat contradictory source statements as separate hypotheses. | Selecting the visually matching convention can accidentally hide a paper error. | Compute each convention, freeze both outputs, and defer source classification to fresh review. |
| Scientific tests are review evidence. | A reviewer must see how reproduction-code error was excluded. | Include `tests/` in the falsification bundle. |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Inferring Hamiltonian sign from the plotted curve | Fig. 2 visually favors antiferromagnetic XXX although Eq. (3) prints the opposite sign. | Bind every convention to explicit source text before looking at pixels. |
| Treating a degenerate ground state as one entropy curve | The literal ferromagnet has both polarized and Dicke ground representatives. | Test degeneracy and report state-dependent observables explicitly. |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Independent small-system formulation | Whenever basis reduction or symmetry sectors could hide a sign/basis bug. | Full Pauli-space and fixed-sector energies agree at N=6. |
| Freeze scientific data before source-image rendering | Any pixel-scored figure reproduction. | RenderContract validates unchanged CSV hashes for both figures. |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Equation/caption physics mismatch | XXX series in Main Fig. 2 | Generate alternative source-consistent models and require fresh falsification review. |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| Review-bundle inclusion of tests | Makes code-fault exclusion independently auditable. | Promoted to `PRAgent-workflow/rr_harness/review_bundle.py`. |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| XY Toeplitz covariance kernel | 1100 points plus checks in a 3.216 s full run. | Keep case-local until another case needs the identical convention. |
| Bit-basis periodic XXX solver | N=20 sector dimension 184,756 with stable Lanczos residual 2.75e-12. | Keep case-local; pattern is reusable but normalization is paper-specific. |

## Harness Backlog Items

Abstract cross-paper lessons should be copied to
`PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`.

Concrete tool, checker, template, field, or workflow changes should be copied to
`PRAgent-workflow/HARNESS_BACKLOG.md`.

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| P0 | Include scientific tests in fresh-review bundles. | T002 causal diagnosis cites independent and convergence tests. | Implemented in commit `a524b31e`. |

## Prompt Or Workflow Changes

- Preserve contradictory printed and caption-implied conventions as separate
  review objects; never choose the higher-pixel-score hypothesis as scientific
  truth.
