# Lessons Learned

Use this file after each reproduction pass. The goal is to extract reusable
lessons from one paper and turn them into better Agent and harness behavior for
the next paper.

## Case Summary

- Paper: *Relaxation toward an Ideal Chern Band through Coupling to a Markovian Bath*
- PaperID: `2511.11394`
- Final status: numerical-feature reproduction for the exact-flow paper
  claims; small-\(q\) Fig. 1 remains partial
- Main reproduced targets: T002–T004, plus the physical features of T001 and
  the independent V001/V002 validations
- Main remaining blocker: undisclosed author numerical metadata and the
  internally inconsistent Fig. 1 normalization

## What Worked

- A gauge-free solid-angle Chern number and exact Fourier shifts made the
  geometric test both short and highly discriminating.
- Normalizing the observable before simulation separated the topological
  coefficient from arbitrary bath strength.
- Negative controls distinguished “topological bands cannot be dark” from the
  false statement that all bands must scatter.
- Reading the actual PDF glyph rather than relying on text extraction recovered
  the crucial \(1/\pi^2\) prefactor.
- A half-cell momentum grid removed symmetry pinning at the bubbling point and
  simultaneously recovered the energy, Chern, and peak-height signatures.

## What Was Difficult

- The paper contains a factor-of-two inconsistency in its Dirichlet prose and
  visible factor-of-four/two plotting conventions.
- The printed LLG equation does not reproduce the source curve's timescale,
  despite extremely small timestep and grid errors.
- Text extraction dropped the superscript in \(1/\pi^2\), producing a plausible
  but wrong first implementation.
- The correct transition is unusually sensitive to whether
  \((\pi,\pi)\) lies exactly on a grid node.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Separate calibrated moments from raw event totals | Open-system rates include arbitrary coupling and detector factors. | Freeze the kernel, unraveling, and normalization before claiming topology. |
| Test source semantics before tuning solvers | A converged mismatch can be an undocumented convention rather than a coding error. | Compare initial ratios, asymptotes, and equation-implied units before fitting time scales. |
| Use topology plus a dark trivial control | A positive response alone does not show a topological obstruction. | Pair a nonzero-Chern family with a constant-projector control. |
| Treat grid origin as part of the numerical method near singular events | A mesh node can pin a symmetry point and eliminate the intended finite-resolution transition. | Test node-centered and midpoint grids before interpreting topology-change failures. |
| Couple multiple observables when reconstructing missing methods | Energy alone admitted wrong stencils; energy, Chern, and peak height selected one consistent scheme. | Require one method to satisfy all linked panels simultaneously. |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Equating a Lindblad decomposition with an observable | “Total activity” changes with jump representation. | Derive a detector-resolved instrument, not merely a master equation. |
| Applying the bound at arbitrary finite \(q\) | The theorem controls the quadratic coefficient. | Extrapolate versus \(q^2\) and report the intercept. |
| Trusting a plotted legend's normalization | Fig. 1's visible curves carry unexplained factors. | Reconstruct dimensionless ratios from analytic bounds. |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Fourier shift for finite momentum probes | Smooth periodic Bloch textures | Gives arbitrary physical \(q\) without grid-locking. |
| Solid-angle Chern discretization | Two-band projectors | Returns exactly stable \(C=1\) while derivative Chern is a convergence diagnostic. |
| Step and grid convergence together | Dissipative PDEs | Rate mismatch remains after \(1.6\times10^{-13}\) step and \(3.1\times10^{-4}\) grid differences. |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Source plot uses undocumented rescaled time/energy | Main Fig. 1 | Compare the printed-equation trajectory with source ratios before claiming reproduction. |
| Topological lower bound is correct but detector interpretation is false | Proposed headline | Require detector-instrument invariance and explicit coupling normalization. |
| Smooth finite-band flow only approaches an unattained infimum | Potential late-time saturation | Track gradient concentration, resolution dependence, and topology through long-time runs. |
| Symmetry-pinned singular grid point suppresses a finite-mesh transition | Exact extended-Hubbard flow | Shift the grid origin and compare several \(N\) before changing the physics. |
| PDF text extraction loses a normalization exponent | Supplemental Eq. (128) | Verify high-impact prefactors against a rendered equation image. |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| Periodic solid-angle Chern helper | Gauge-free and fast for any two-band texture | `rr_harness` geometry utilities |
| Finite-\(q\) moment convergence check | Tests whether an event-weight observable really measures a metric | formula/numerics validation helper |
| Source normalization semantic audit | Detects equation/legend/curve factor conflicts | case audit extension |
| Midpoint-grid singularity diagnostic | Detects artificial pinning at high-symmetry points | target-readiness numerical-method checklist |
| Low-rank trigonometric convolution | Converts a dense extended-Hubbard convolution into five moments | case pattern, promote after reuse |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| Vectorized QWZ/LLG validation | Full feature run and two refinements take 2.91 s on Apple M4 | QWZ/LLG case-local |
| FFT periodic shift and solid-angle topology | \(N=121\) static scan included in same run | promote after a second case reuses them |

## Harness Backlog Items

Abstract cross-paper lessons should be copied to
`private validation harness/REPRODUCTION_EXPERIENCE.md`.

Concrete tool, checker, template, field, or workflow changes should be copied to
`private validation harness/HARNESS_BACKLOG.md`.

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| high | Add a detector-normalization checklist for Lindblad click claims | raw activity can be scaled to zero independently of topology | `copied_to_backlog` |
| medium | Add equation/caption/curve normalization consistency gate | factor and time-scale conflicts in Main Fig. 1 | `copied_to_backlog` |

## Prompt Or Workflow Changes

- Require “observable definition → normalization → limiting coefficient →
  topology” as four separate gates for open-system sum-rule proposals.
- Treat a converged source mismatch as a result; do not tune an undocumented
  time scale merely to improve visual similarity.
