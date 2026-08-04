# Lessons Learned

## Case Summary

- PaperID: `2607.27060`
- Final status: complete frozen-scope reproduction with two paper-side findings
- Reproduced targets: `FIG002A-D`, `FIG003A-D`
- Compute blockers: none
- Evidence limits: no author numeric table or benchmark dataset

## What Worked

- A single monotone resource-bound model covered all eight panels.
- Log-domain comparisons made very large \(N\) values numerically routine.
- An independent Lambert-\(W\) inverse caught binary-search errors without
  relying on author results.
- Separating scientific generation from post-generation pixel tuning preserved
  provenance while achieving 99.74 pixel fidelity.
- Cross-target assertions exposed a narrative error that isolated panel checks
  would miss.

## What Was Difficult

- The XX plotting grid is absent from the prose and required frozen source-only
  method metadata.
- The reported \(\lambda\) values do not follow from the documented Choi-bound
  calculation under either the literal equation or source snapshot
  dissipator convention.
- “Fewest steps therefore lowest gates” is not valid before accounting for the
  second-order factor of two.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Validate claims across targets | A correct panel can still contradict the paper's prose. | Add claim-level checks after all target checks pass. |
| Separate parameter audits from panel inputs | A reported parameter may be usable yet methodologically unexplained. | Preserve the reported value for reproduction and record the derivation finding separately. |
| Invert monotone thresholds independently | Two implementations of the same search can share a control-flow bug. | Prefer a closed form or different solver as the cross-check. |
| Keep pixel work downstream | Source styling must not contaminate generated science. | Freeze CSVs before loading source panels. |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | Prevention |
| --- | --- | --- |
| Equating fewer steps with fewer gates | Second order uses \(2MN\), creating small-\(M\) crossovers. | Check the final resource observable, not only its intermediate variable. |
| Treating reported constants as derived | Reported \(\lambda\) values were not reproducible from Eq. (32). | Attach a source/method audit to every derived global constant. |
| Trusting visual agreement as science | Near-identical panels could be copied or digitized. | Require independent-numerics provenance and target checks before pixel comparison. |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| monotone integer-minimum checker | Verifies \(f(N)\le\epsilon<f(N-1)\) exactly | future generic numerical-check helper |
| cross-target claim checker | Detects conclusions that fail after derived-cost conversion | future claim-ledger validation pattern |
| source-convention parameter audit | Separates equation, code, and reported-value conventions | case-local unless repeated |

## New Failure Modes

| Failure mode | Where it appeared | Detection |
| --- | --- | --- |
| reported global constant not derivable from stated method | \(\lambda\) in Section 5.3/5.4 | independently reconstruct the local Choi bound under both equation and source conventions |
| resource ranking inferred from an intermediate quantity | second-order randomised \(N\) versus \(g=2MN\) | compare final resource values across all methods at every shared grid point |
| prose conclusion contradicted by its own numerical panels | small-\(M\) gate-complexity ordering | bind narrative claims to cross-target executable assertions |

`copied_to_backlog`: not performed because this frozen Trial explicitly
forbids modifications outside `case/2607.27060`.

## Efficient Reproduction Implementations

| Implementation | Evidence | Scope |
| --- | --- | --- |
| log-domain precision evaluation | eight scientific targets in 1.130575 wall seconds | reusable pattern |
| scalar binary search | 48 exact minima without simulation trajectories | case-local model |
| style-only pixel renderer | eight panels in 1.245871 wall seconds | case-local |

## Workflow Recommendation

For similar formula-driven papers: read the full paper, derive the monotonic
model, verify with a mathematically different reference, run guarded targets,
then add cross-target claims and only afterwards activate source-pixel
comparison.
