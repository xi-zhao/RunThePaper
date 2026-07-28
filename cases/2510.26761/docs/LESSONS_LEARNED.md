# Lessons Learned

## Case Summary

- Paper: *Sufficient Wigner Negativity Implies Genuine Multipartite
  Entanglement*
- PaperID: `2510.26761`
- Final status: `numerical_feature_reproduction`, score 85
- Main reproduced targets: both main figures and three invariant validations
- Main blocker: one source-printed threshold conflicts with the source-printed
  normalized state; Fig. 1 rendering settings are undisclosed

## What Worked

- Expanding the states in collective Fock modes before coding reduced all
  numerical objects to finite sums.
- Independent parity and convolution identities provided grid-free anchors for
  the two Fig. 1 witnesses.
- The analytic W-state formulas made Fig. 2 reproducible without digitizing a
  single source pixel.
- A stricter convergence gate caught a \(5.72\times10^{-6}\) last-grid change;
  one finer grid confirmed the requested \(5\times10^{-6}\) tolerance.

## What Was Difficult

- The paper's Fig. 1 inequality is internally inconsistent. Treating the paper
  as automatically correct would have made the numerical implementation look
  wrong.
- The Fig. 1 central plot contains numerical isosurfaces embedded in a
  schematic, so classification had to separate the physical field from its
  undisclosed presentation settings.
- The theorem-1 corrected certification margin is small, requiring convergence
  evidence rather than a single attractive heat map.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Recompute every quoted bound from the displayed state or model | source prose and source equations can disagree | store source-printed and state-derived values side by side |
| Use independent invariants before visual comparison | a plausible plot can hide normalization or sign errors | require normalization, signed integrals, and limiting cases before rendering |
| Separate numerical content from schematic composition | mixed figures otherwise become incorrectly excluded or overclaimed | classify panels by scientific object, not by the figure's overall appearance |
| Tight-margin witnesses need a convergence ledger | one grid can cross a threshold accidentally | compare at least two sufficiently fine grids and preserve the margin |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Trusting a printed numeric inequality | `+56` conflicts with the state-derived `+52` | derive the signed integral from parity before quadrature |
| Confusing the Wigner zero radius with the measurement radius | the negative disk ends at 0.2887, while certification needs 0.6992 | distinguish sign-change geometry from absolute-volume threshold |
| Counting 49 matrix entries as 49 measurements | symmetry leaves 19 differences and ten independent values | enumerate and deduplicate the complex differences explicitly |
| Calling reconstructed 3D styling exact | isosurface levels and camera are missing | keep the figure exploratory even when the underlying field is exact |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Collective-mode transformation first | symmetric multimode phase-space slices | reduces \(|W_3\rangle\) to one Fock excitation |
| Analytic control plus independent quadrature | closed-form integral is printed | agreement reaches \(1.1\times10^{-16}\) |
| Hermitian eigensolver and point-count check | characteristic-function witnesses | reproduces one negative eigenvalue and \(0.0175804\) |
| Explicit source-inconsistency verdict | printed claim fails its own definitions | preserves both thresholds and the scientific consequence |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| source-state/quoted-bound inconsistency | Fig. 1 End Matter | recompute quoted scalars from normalized source inputs before numerical execution |
| threshold-margin fragility | corrected Fig. 1 witness | record convergence and both sides of the inequality |
| mixed schematic/numeric figure misclassification | Main Fig. 1 | maintain a panel/object ledger inside a single source figure |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| sparse finite-Fock Wigner evaluator | many CV papers publish finite Fock expansions | future shared CV utility after a second case |
| source-quoted scalar consistency check | catches transcription and paper errors before simulation | harness backlog |
| dual-value discrepancy record | prevents silently replacing the source with a correction | project manifest/report schema |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| vectorized Fock matrix elements | complete Fig. 1 run in 1.37 s | candidate for promotion after reuse |
| broadcast polar quadrature | \(800\times3072\) result in under 0.4 s | generic pattern |
| FFT smoothing with analytic anchor | grid origin agrees to \(2.8\times10^{-15}\) | generic pattern |
| W-state closed forms | exact and immediate | case-local |

## Harness Backlog Items

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| high | Add a first-class `source_inconsistency` finding that stores source value, derived value, consequence, and target-stage cap | +56 versus +52 changes whether the witness is violated | copied as `H083` |
| medium | Allow mixed schematic/numeric figure items to declare separate presentation and numerical subobjects | Fig. 1 contains both | covered by existing `H024`; new evidence recorded |
| medium | Add threshold-margin plus convergence checks to numeric witness contracts | corrected margin is \(2.56\times10^{-4}\) | copied as `H084` |

## Prompt Or Workflow Changes

- Before coding, recompute every paper-quoted scalar from the displayed
  equations and normalized inputs.
- When a source contradiction appears, preserve the source statement, derive
  the consistent alternative, and downgrade only the affected target.
- Do not let a source inconsistency lower unrelated exact targets in the same
  paper; score per figure first, then aggregate.
