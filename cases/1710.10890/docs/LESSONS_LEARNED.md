# Lessons Learned

## Case Summary

- Paper: *Self-Bound Quantum Droplets of Atomic Mixtures in Free Space*
- PaperID: `1710.10890`
- Final status: partial numerical-feature reproduction
- Main reproduced targets: interaction lane, phase boundary, population ratio,
  critical number/size, levitation potential, and expansion proxy
- Main blockers: unpublished interaction model, experimental arrays, Fig. 4/S2
  atom numbers, an unrun 80 GiB GPU campaign, and an inconclusive Fig. 3(b)
  method-equivalence gap

## What Worked

- Reducing the droplet problem to the universal Petrov radial equation recovered
  the printed dimensionless critical-number anchors without author code.
- A strictly isolated numerical lane produced seven hash-frozen datasets in
  1.11 s with zero forbidden file accesses.
- Post-freeze visual comparison improved layout diagnosis while preserving the
  numerical arrays exactly.
- Reading the supplement's definition of the signed force gradient corrected a
  genuine sign-convention error in T006 before acceptance.
- Re-reading the simulation section showed that the initial numerical array is
  not indispensable: the paper specifies a trapped state-2 ground-state
  preparation that can be implemented independently.
- A single campaign object now expands four physical scenarios across
  production, spatial-refinement, and time-refinement profiles, with
  task-hash-bound recovery and one scientific finalizer.

## What Was Difficult

- The paper's magnetic-field interaction curves depend on an unpublished
  coupled-channel model, so later citable parameter rows were needed and marked
  `paper_subset`.
- Main Fig. 3(b) does not state a width definition that explains why its plotted
  stable/metastable ordering opposes independently converged profiles.
- Experimental points and Fig. 4/S2 atom numbers are not published as arrays;
  source pixels cannot substitute for scientific inputs. Initial GPE fields,
  however, are generated from the stated preparation and need not be supplied
  by the authors.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Artifact validity and paper agreement are distinct | a converged calculation can still falsify the plotted claim | keep target artifact checks separate from paper-consistency assertions |
| Signed observables need an explicit convention | curvature, force gradient, and stability signs can be visually reversed | write the plotted observable, including sign, into the equation card and tests |
| Parameter provenance limits the lifecycle state | matching shape with reconstructed parameters is not paper-exact | require per-target `parameter_match` and cap final status accordingly |
| Compute may defer execution, not implementation | a future A100 allocation is only useful if the exact runner, config, outputs, recovery and acceptance already exist | ship the complete paper-scale contract and mark the remaining parameter claim honestly |
| Observable definitions are method inputs | Main Fig. 4 uses Gaussian 1/e² width while S2 uses vertical TF radius | derive moment conversions explicitly and test/report both raw RMS and paper observables |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Swapping branches to improve pixel score | T005 would look better if stable/metastable lines were exchanged | freeze physical branch identity before rendering and fail the scientific assertion |
| Treating a proxy as an exact solve | frozen T007 qualitatively suppresses expansion but misses absolute radii | retain it as baseline, add the method-faithful GPE lane, and keep both limited by missing N |
| Letting source figures influence physics | paper panels reveal line locations and labels | enforce forbidden roots during numerics and record the access manifest |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Solve universal dimensionless equations once | a paper maps one universal solution across parameters | T004/T005 reuse the Petrov branches efficiently |
| Inspect equations and high-resolution panels after freeze | sign/legend semantics remain ambiguous | resolved T006's plotted force-gradient sign without tuning arrays |
| Preserve failed comparisons | independent numerics disagree with a source figure | T005 remains visible with a 26.3797 scientific-region score |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Branch identity disagrees with line style | Main Fig. 3(b) | assert physical ordering before render and compare each declared branch separately |
| Source defines a signed derivative indirectly | Supplement Fig. S1(c) | trace the plotted label back to the force/potential derivative convention |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| Scientific-theory color/line mask | removes experimental markers while retaining theory curves | keep case-local until validated across more styles, then consider harness helper |
| Pre-render branch-identity assertion | prevents cosmetic relabelling from hiding physics failure | target-contract checker extension |
| Compute-worthiness gate | avoids remote runs for missing-input cases | harness planning/reporting layer |
| Task-hash-bound scientific checkpoints | prevents changed configs from resuming stale wavefunctions | general large-scale numerical runner contract |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Scope |
| --- | --- | --- |
| Shared universal radial profiles | full T001--T007 run takes 1.105981 s | keep in the case physical model |
| Vectorized levitation quadrature | dense three-panel curves in the same run | keep case-local |
| Isolated bundle plus hash manifest | 651 events, zero forbidden access | existing harness capability |

## Harness Backlog Items

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| P1 | distinguish valid artifact from agreement with paper at target level | T005 artifact passes while the paper-consistency assertion fails | candidate |
| P1 | add explicit branch-identity/legend contracts | T005 could otherwise be cosmetically swapped | candidate |
| P2 | record plotted signed-observable conventions | T006 initially used the opposite curvature sign | candidate |

## Prompt Or Workflow Changes

- Require a pre-render declaration of branch identity, sign convention, and
  plotted observable.
- Allow missing-input sensitivity campaigns only with explicit assumptions;
  never upgrade them to paper-exact agreement.
- Require code-ready paper-scale contracts before accepting compute or hardware
  as an execution deferral.
