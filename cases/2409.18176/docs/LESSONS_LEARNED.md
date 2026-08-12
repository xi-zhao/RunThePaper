# Lessons Learned

## Case summary

- PaperID: `2409.18176`
- Status: partial; `feature_not_accepted`
- Passing targets: T001--T005, T007, T010 under their declared proxy/subset
  boundaries
- Failed targets: T006, T008, T009

## What worked

- A positive-semidefinite collision representation made conservation and
  stability visible rather than implicit.
- Separate Galerkin, collocation, Kubo, and direct-three-fluid implementations
  exposed method disagreement that a single solver would have hidden.
- Freezing data before extracting source figures prevented visual tuning from
  contaminating physics.
- A paper-scale runner was written even though its campaign was not locally
  executed.

## Reusable lessons

| Lesson | Why it matters | Future rule |
| --- | --- | --- |
| Author repositories can exist even in a “no-source” candidate list | candidate metadata may be wrong | check availability, record it, and keep the blind boundary |
| Analytic parity can coexist with paper-level failure | internal correctness is not reproduction correctness | keep invariant checks and paper comparisons as separate gates |
| Closed forms need dimensional checks | copied algebra can silently preserve a typo | compare literal, corrected, and direct-matrix forms |
| Kubo/Boltzmann agreement needs independent discretization evidence | two formulas alone do not prove numerical parity | require convergence and a second regularization before blaming the paper |

## New Failure Modes

| Failure mode | Evidence | Detection |
| --- | --- | --- |
| missing mass factor in nested analytic denominator | direct/corrected parity `1.67e-16`, literal gap `1.95e-3` | dimensional analysis plus direct solve |
| internally stable but paper-inconsistent Kubo difference | PSD/residual checks pass while T009 gap is `11.2776` | keep paper-level magnitude assertion essential |
| source crop similarity tempting premature parameter tuning | visible amplitude gaps in comparison boards | enforce post-freeze RenderContract and hash recheck |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| literal/corrected/direct closed-form triage | separates source algebra issues from solver bugs | future Harness formula-audit helper |
| post-freeze CSV hash guard | prevents RenderContract from changing scientific arrays | keep as required case-local comparison pattern |

## Harness backlog candidate

Add a generic dimensional-consistency audit for closed hydrodynamic formulas
whose coefficients are printed with compound units.  This case records the
lesson locally; it does not edit the shared Harness backlog from a case-only
branch.
