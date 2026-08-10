# Lessons Learned

## Case summary

- Paper: *Quantum Machine Learning in Feature Hilbert Spaces*
- Coverage: all 14 numerical panels and the loss inset.
- Main success: the complex kernel ambiguity was resolved from the paper's own absolute-square rule and independently verified against the Fock series.
- Main blocker: missing random/data/training metadata for Figs. 5--8.

## Reusable lessons

| Lesson | Why it matters | Future rule |
| --- | --- | --- |
| A method can be exact while its benchmark is not | Printed equations do not imply printed random instances | Track formula status and parameter status separately |
| Complex quantum overlaps need an explicit real-kernel convention | Passing a complex Gram matrix to a classical learner can silently change the model | Trace the paper's realification rule and verify PSD |
| A caption's panel count is part of scope | The paper has only four numerical figures but 14 numerical subpanels | Enumerate each subpanel before coding |
| Training success is not paper-exact evidence | Many independent seeds can reach similar accuracy | Preserve reconstructed status until seed/data/optimizer contracts are known |
| Hardware choice depends on the evidence scale | cutoff-8 dense states finish locally, while cutoff-32 convergence benefits from sector factorization and A100 execution | Profile the accepted run and the convergence campaign separately |
| Training mismatch is not automatically a paper error | omitted seeds/cutoffs/optimizer choices can move the full decision map | Require paper-exact metadata, independent checks and fresh-context falsification before an author-error claim |

## New Failure Modes

- The first local run exposed a perceptron grid-shape indexing error before attestation.
- The first complete run exposed a NumPy boolean serialization error after all numerics; the isolated rerun then produced a clean attestation.
- Harness checks caught missing equation-card gate metadata and an inconsistent paper-exact parameter mapping before commit.

## Reusable Checks Or Tools

- Keep the formula-gate checker: it caught missing source/derivation evidence before state derivation.
- Keep target-contract equality checks: they prevented a paper-exact label whose human-readable parameter dictionaries differed.
- Keep the isolated runner's source-root denylist and post-freeze hash check for every learned-figure case.

## Harness backlog

No new harness code is required. A possible future checker could warn when a case calls a config `paper_exact.json` while individual targets explicitly carry reconstructed parameters; current target-level state already prevents a false completion claim.
