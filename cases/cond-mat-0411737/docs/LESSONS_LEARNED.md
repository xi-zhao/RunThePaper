# Lessons Learned

Use this file after each reproduction pass. The goal is to extract reusable
lessons from one paper and turn them into better Agent and harness behavior for
the next paper.

## Case Summary

- Paper: *Quantum Spin Hall Effect in Graphene*.
- PaperID: `cond-mat-0411737`.
- Current status: `in_progress`; the v11 artifact is valid and attested, and the
  v18 fresh-context review passes with complete scope. Literal completion is
  capped by publication/external-input limits, not by an open code defect.
- Main reproduced scope: 13 targets and 40 runner assertions across bands,
  topology, boundaries, transport, interactions, microscopic projection and RG.
- v7 findings repaired at implementation/contract level: physical branch
  selection, intervalley-path attribution, independent screening generation,
  Figure 1 exactness, and the two rounded material-scale claims.

## What Worked

- A geometric clean-room ribbon construction reproduced the topological edge
  crossing without author code, arrays or digitized curves.
- Symmetry, topology, continuum and material-scale checks made code-fault
  attribution substantially stronger than visual comparison alone.
- Separating the numerical runner from rendering produced a clean attestation
  without relaxing process isolation.
- The historical atomic review found defects hidden by passing machine
  assertions; a new post-repair review then verified that those defects were
  closed instead of trusting the reproducer's own explanation.

## What Was Difficult

- A visually plausible honeycomb cut can actually be a bearded edge; site
  coordination and the flat-band momentum interval must be tested.
- The paper's missing strip width affects branch density even though the
  central topology is width-stable.
- A Kramers-degenerate state is not automatically the desired edge branch; a
  selector must track physical identity and beat a geometric localization
  baseline.
- A coarse two-dimensional momentum grid can report a healthy-looking bulk
  gap even when a continuous optimizer finds an exact closing between grid
  points.
- Re-fitting a formula-generated `1/q` curve is circular evidence, even when
  the fitted exponent is numerically perfect.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Keep Matplotlib out of the scientific runner | Font discovery may spawn processes and weaken/violate isolation | Freeze arrays first; render in a separate hashed channel |
| Test boundary topology, not only Hermiticity | A wrong edge termination can still yield a valid Hermitian matrix | Assert coordination and a known edge-state landmark |
| Distinguish science from finite-size presentation | Missing width changes branch count but not the QSH invariant | Report exact affected scope and use width convergence |
| Track observable identity, not eigenvalue position | Rashba shifts an edge crossing away from zero | Follow eigenvectors across parameter and width sweeps |
| Falsify gapped interpolation continuously | A 24x24 grid reported about 0.143 t while a continuous search found a gap below 1e-16 t | Minimize the direct gap over momentum and path coordinate before accepting a topological connection |
| Derive before fitting | A constructed power law will always reproduce its own exponent | Freeze raw polarization/susceptibility output before constructing screened interaction |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Wrong honeycomb termination | Same-row A/B retention produced a bearded edge | Encode edge coordination and Kramers-crossing tests before full runs |
| Renderer inside sandbox | Matplotlib attempted two `fc-list` child processes | Make RenderContract a separate post-freeze entrypoint |
| Treating absent width as paper exact | Foreground line density differs although science passes | Use `paper_subset` and a publication-underspecified causal diagnosis |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Hash scientific data before opening source figures | Every figure reproduction | v11 preserves band CSV hash `7ac055bd...97897f7` before rendering and comparison |
| Use symmetry-unique scientific crops | Source contains an inset over a duplicated symmetric region | Left-half score 90.3679; full canvas remains diagnostic only |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Benign library subprocess attempts | v1 isolated run, Matplotlib font scan | Fail closed on every subprocess and record the denied events |
| Manuscript cross-reference drift | Three equation numbers | Fresh-context reviewer should check prose/equation bidirectional consistency |
| Passing circular science check | Screening code inserted the expected law and fitted it back | Require an upstream independently computed observable and convergence evidence |
| Symmetry over-attribution | A generic T-odd intervalley bridge was called a uniform-field path | Test every operator against all remaining spatial symmetries and physical source terms |
| Grid-induced false topology | A coarse mesh missed a gap closing in a proposed bulk interpolation | Add a continuous minimizer or an adaptive certified bound, not just a denser plot grid |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| Frozen-data RenderContract guard | Proves plotting cannot alter numeric arrays | Harness rendering contract |
| Boundary-coordination invariant | Catches geometrically wrong but Hermitian lattice cuts | Case method-test pattern |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| Reused geometry plus conserved-spin blocks | complete v11 scientific channel in 243.246548 s attested | Keep lattice kernel case-local |
| Separate rendering/comparison channel | v11 attestation, zero forbidden access | Promote workflow pattern |
| Streaming full-k branch diagnostics | all subcritical zigzag/armchair widths resolved without storing full spectra | Keep spectral-flow selector case-local; promote the evidence contract |

## Harness Backlog Items

Abstract cross-paper lessons should be copied to
`PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`.

Concrete tool, checker, template, field, or workflow changes should be copied to
`PRAgent-workflow/HARNESS_BACKLOG.md`.

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| P1 | Formalize numeric-run/render-run separation as a Harness contract field | v1 failed only because Matplotlib probed fonts; v2 passed unchanged science | proposed |

## Prompt Or Workflow Changes

- Always classify missing publication metadata at the exact affected target
  scope; do not report a generic “not paper exact” label.
