# Lessons Learned

## Case Summary

- Paper: *Exact Fractionalized Ground States in an Extended Spin-1 Kitaev Chain*
- Paper ID: `2510.12880`
- Current status: partial whole-paper reproduction; historical Fig. 5 score `95/100`
- Item measure: 4/9 covered, coverage `44.44%`, fidelity `92.03`, degree `40.90`
- Main reproduced targets: V001, V002, and both panels of Main Fig. 5
- Main residuals: V003-V007 are unimplemented scientific items; one bounded
  ground-state source-point discrepancy and missing author solver metadata remain

## What Worked

- Deriving the Cartesian basis first exposed diagonal conserved sectors and
  reduced the paper-scale problem from \(3^{12}\) states to blocks of a few
  hundred.
- Building the physical MPS from the compact contraction formula was safer than
  copying long printed tensor lists.
- Exact-point zero energy, full-space small-\(N\) spectra, and sector-support
  tests caught tensor-index mistakes before curve generation.
- Digitized markers were kept as reference data, while every generated point
  came from independent diagonalization.

## What Was Difficult

- The source contains three semantic/typographic ambiguities that directly
  affect code: a missing \(\pi\), two wrong tensor superscripts, and an axis
  labeled “overlap” that numerically means squared overlap.
- The physical-leg projection initially used the wrong source-basis row order.
  The MPS-sector support test exposed it immediately.
- One paper marker disagrees despite all algebraic checks and 49 other curve
  values agreeing. That required an evidence policy, not parameter tuning.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Observable names are not sufficient specifications | “overlap” may mean amplitude, squared amplitude, or subspace weight | use a visible anchor point or table value to disambiguate the mathematical observable before opening the numerical gate |
| Exact symmetry reduction is not reduced-scale evidence | a small block can still be the complete paper model | record the proof of invariance and full-space partition so scoring does not penalize exact block diagonalization |
| Source typos should be resolved by invariants | copying a malformed equation can silently destroy a conserved quantity | preserve the printed form, corrected form, and invariant that selects the correction |
| One isolated marker should not drive model changes | local fitting can corrupt a globally validated derivation | require residual, trend, negative-control, and remaining-point checks before classifying an isolated source discrepancy |
| A schematic can carry an adjacent quantitative result | excluding the picture does not exclude a theorem or degeneracy stated beside it | enumerate the display and the independent claim separately, then mark the claim covered or uncovered |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| basis-order mismatch | projections were listed as \(+1,-1,0\) while the transform rows were \(+1,0,-1\) | test support in the exact symmetry sector before any overlap calculation |
| arbitrary degenerate eigenvectors | the first-excited manifold is \(N\)-fold degenerate | compare a matching symmetry sector or use a basis-independent projector |
| image-driven implementation | two curves look easy to fit directly | derive the Hamiltonian, MPS, and observable semantics first |
| overreacting to one point | one of 50 values exceeded pixel tolerance | report the point and seek author provenance; do not introduce a special-case factor |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| full-space parity test | after implementing a symmetry block | \(N=4\) sector spectra match the full Hamiltonian |
| exact-point invariant test | when a model has a frustration-free point | every constructed MPS has zero energy at \(\theta=\pi/4\) |
| observable anchor check | when captions use informal language | squared amplitudes reproduce the visible \(N=12,\theta=0\) points |
| reference/generated provenance split | whenever curves are digitized | source CSVs are labeled separately and never feed the Hamiltonian |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| caption-semantic mismatch | “overlap” actually means squared fidelity | test all plausible conventions against one source anchor and physical bounds |
| internally repairable source typo | odd-bond rotation and \(s=0\) tensor definitions | run stated identities such as \(W^2=1\) and compare compact definitions to expanded matrices |
| isolated source/numeric discrepancy | Main Fig. 5(a), \(10^\circ,N=12\) | emit per-point error diagnostics and the worst-point coordinates |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| observable-semantics anchor gate | prevents amplitude/probability and norm/squared-norm confusion | formula gate helper |
| worst-point curve diagnostic | distinguishes global model mismatch from one source outlier | comparison harness |
| exact-sector certification record | prevents exact symmetry reductions from being mislabeled reduced-scale | target parameter contract |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote |
| --- | --- | --- |
| Cartesian conserved-sector enumerator | \(N=12\) blocks shrink to 322 and 288 states | keep case-local |
| basis-independent eigenspace fidelity | removes arbitrary degenerate eigenvector choices | promote as a documented pattern |
| colored-marker source digitizer | all 50 markers extracted with pixel uncertainty | keep case-local until another paper needs the same marker geometry |

## Harness Backlog Items

The following recommendations were `copied_to_backlog` under case
`2510.12880`:

| Priority | Improvement | Evidence | Status |
| --- | --- | --- | --- |
| high | add an observable-semantics anchor gate | amplitude versus squared amplitude changes both panels | copied_to_backlog |
| medium | standardize worst-point and inlier-count curve diagnostics | one isolated discrepancy should not be hidden in a mean error | copied_to_backlog |
| medium | record exact symmetry reduction separately from numerical scale reduction | the complete \(N=12\) model fits because of an exact block decomposition | copied_to_backlog |

## Prompt Or Workflow Changes

- Before numerical code, require one explicit sentence defining what every
  plotted ordinate mathematically means.
- Before accepting a symmetry-reduced run, require a proof or regression test
  that the blocks partition the full Hilbert space.
- When only one reference point fails, require a named worst-point record and a
  no-tuning justification.
