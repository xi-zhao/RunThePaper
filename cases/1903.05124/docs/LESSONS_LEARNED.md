# Lessons Learned

Use this file after each reproduction pass. The goal is to extract reusable
lessons from one paper and turn them into better Agent and harness behavior for
the next paper.

## Case Summary

- Paper: *Quantum Error Correction in Scrambling Dynamics and Measurement-Induced Phase Transition*
- PaperID: `1903.05124`
- Final status: complete numerical feature reproduction; 20/44 numerical items reproduced at paper scale and 24 more at feature scale.
- Main reproduced targets: analytic decoupling and channel-capacity claims plus all six numerical targets, including T006's three block-size scaling panels.
- Main blockers: none for the frozen scientific scope; paper-scale T001/T004/T005/T006 precision remains an optional upgrade.

## What Worked

- Reading the source TeX and rendering every standalone figure before target selection exposed 44 numerical panels/insets and prevented schematic panels from being mislabeled as reproduced data.
- A frozen early-time protection check rejected the first visually plausible S3 run and exposed that the brick-wall odd/even schedule was reversed.
- Model-revision-bound per-setting checkpoints made the 1,920-trajectory paper run resumable while preventing the rejected schedule's data from being reused.
- A persistent process pool completed 455 heterogeneous T001 settings without macOS semaphore exhaustion, while the same trajectory supplied both half-chain and `I3` observables for later targets.
- A coordinate-only midpoint campaign reused the T001 scientific base without reusing its values: 2,048 new trajectories doubled each T005 curve to 17 points and removed every fit-boundary warning.
- Reusing those independently simulated trajectories for a fresh EQC007 half-chain fit completed all ten T004 items in `56.65 s` without rerunning dynamics or consulting source curves.
- A three-stage T006 campaign used generated `I3` values to choose only interval coordinates, then generated a separate critical-entropy ensemble. It completed all six paper `m` values in `771.05 s` and resumed for fit/check changes in `40.18 s` without rerunning trajectories.

## What Was Difficult

- The authors specify the ensemble and main parameters but not seeds, every sampling grid, or exact equilibration windows. Independent convergence rules must replace these missing metadata without visual fitting.
- The S3 caption calls its error bars standard deviations, but trajectory-level SD is about `0.6–0.9` while the raster matches SE about `0.04–0.06`; source prose and plotted semantics cannot both be accepted silently.
- A naive maximum-gradient transition window selected the wrong low-`p` shoulder for shallow depth. An independently frozen volume-law-to-area-law threshold was needed before fitting; published Table SI values remained post-fit acceptance only.
- Nine points per transition curve located `p_c` reliably but left `nu` boundary-sensitive. Midpoint refinement fixed the boundary pathology, yet `L≤24` and eight realizations per cell still produced excessive depth variation; denser `p` sampling cannot substitute for larger finite sizes/statistics.
- An initial T004 check incorrectly required the normalized-density slope to grow with size. Eq. (9) constrains extensive entropy `S`, whose derivative scales as `L^(1/nu)`; for `S/L`, the slope may decrease when `nu>1`. Re-deriving the invariant fixed the test without relaxing its threshold.
- T006's raw `alpha` span slightly exceeded a naive constancy threshold even though every estimate carried a large finite-sample uncertainty. Testing the actual claim required an uncertainty-weighted constant fit: reduced chi-square `1.730`, maximum pairwise separation `2.353 sigma`, and negligible `m` correlation.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Count visible numerical insets as explicit scope items. | Insets often contain an independently fitted scientific observable. | Freeze each inset in `figure_coverage.json` before execution. |
| Separate analytic claim completion from numerical-figure completion. | A paper may contain proved central claims and still have many unexecuted simulations. | Let the claim graph resolve derivations while targets remain active. |
| Freeze the mapping between physical time labels and staggered circuit layers. | A one-step parity shift preserves plausible entropy growth but reverses the measurement-protection conclusion. | Derive and unit-test which layer crosses each observed bipartition before a long run. |
| Validate uncertainty labels against raw sample scaling and the source raster. | SD, SE, confidence intervals, and time-averaged fluctuations differ by large factors yet are often mislabeled. | Persist all defensible uncertainty estimators, render the source-consistent one explicitly, and record any prose/raster conflict. |
| Reuse one scientific trajectory across observables, not across claims blindly. | Half-chain entropy and `I3` share dynamics but require different boundary/subsystem contracts. | Persist raw observable ensembles once, then let each target apply its own frozen fitting and acceptance rules. |
| Separate grid-resolution uncertainty from finite-size/statistical uncertainty. | Adding more `p` points can stabilize the optimizer without establishing the thermodynamic exponent. | After fit-boundary warnings clear, stop tuning the grid and increase `L`/realizations; retain a partial verdict until then. |
| Derive validation invariants in the same normalization as the paper's scaling ansatz. | Dividing an extensive observable by system size changes its derivative exponent and can make a correct transition fail an incorrect test. | Write the scaling law next to each numerical check and unit-test it on synthetic data before interpreting a failure. |
| Test “constant within error bars” with uncertainty-aware statistics. | A raw max-minus-min range ignores heteroscedastic uncertainty and can reject mutually compatible estimates. | Freeze reduced chi-square, standardized pairwise separation, and trend criteria before interpreting noisy fitted coefficients. |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Declaring pixel targets before scientific data exists | Pixel coverage correctly rejected nonexistent layout artifacts. | Use `scientific_target_blocked` until independent generated data passes. |
| Treating a printed numerical table as a figure | Table SI is useful evidence but outside the user-selected figure-rendering scope. | Bind table values to scientific checks without rendering them. |
| Letting a smooth upper curve validate the time schedule | The reversed schedule reproduced steady densities but made strong-scrambling odd-step `Delta S_meas` strongly negative from the start. | Require a time-resolved invariant tied to the caption/footnote, not only final-state agreement. |
| Recreating process pools inside dense parameter loops | Hundreds of short-lived pools exhausted macOS semaphores during T001. | Keep one persistent pool per campaign and checkpoint each immutable parameter cell. |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Render and inspect all source figure assets during mapping | Multi-panel theoretical papers | Revealed S4's three numerical collapse insets and S3's 16 observable panels. |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Pixel contract points to undeclared artifacts | Initial scope validation | `check_pixel_coverage.py` fails closed on unknown PixelLayoutTargets. |
| Staggered-step parity inversion | First T003 feature run | Assert whether each physical step crosses the measured cut and reject when the paper's early-time protection signature fails. |
| Caption/raster uncertainty mismatch | T003 lower panels | Compare trajectory SD, SE, and visible error-bar scale; preserve both numeric columns and flag the inconsistency. |
| Adaptive fit window locks onto a noncritical shoulder | First T001 transition campaign | Determine the volume-to-area bracket from an independent order-parameter threshold, assert that the fitted `p_c` is interior, and report exponent boundary hits. |
| A dense-looking curve is mistaken for a precise exponent | First T005 fit and midpoint refinement | Track fit-boundary status, leave-one-size-out drift, mean exponent, and exponent span separately; do not promote when only grid resolution improves. |
| A normalized plot is treated as the fitted extensive observable | First T004 validation pass | Derive the expected size power before comparing slopes; here `dS/dp`, not `d(S/L)/dp`, is the sharpening invariant. |
| Raw coefficient range is mistaken for significant parameter dependence | First T006 validation pass | Fit a weighted constant and check reduced chi-square, pairwise standardized separation, and correlation; keep the raw range as a diagnostic only. |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| Visible-inset coverage check | Prevents an inset from disappearing under its parent panel | Harness coverage/audit layer after more case evidence. |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| Phase-aware Clifford trace from a binary kernel | Pending T002 benchmark | Keep case-local until independently tested and reused. |
| Python-int stabilizer generator columns | T003 paper scale: 1,920 trajectories in `636.96 s` on eight workers | Keep domain implementation case-local; reuse for T001/T004–T006. |
| Revision-bound parameter checkpoints | A completed paper rerender resumes in under one second without recomputing 636.96 s of trajectories | Promote the revision-binding pattern, not the paper parameter grid. |
| Persistent shared-observable process pool | T001 completed 3,804 trajectories/455 settings in `651.50 s` wall time after short-lived pools exhausted semaphores | Keep stabilizer logic case-local; consider promoting the pool/checkpoint orchestration pattern. |
| Midpoint-only transition refinement | T005 added 2,048 trajectories in `590.18 s`, doubled grid resolution, and removed all exponent-boundary hits without repeating base cells | Keep sampling policy case-local; reuse the coordinate-only refinement pattern. |
| Cross-target observable reuse with a fresh formula fit | T004 consumed independently generated half-chain rows from T001/T005 and completed a new 8-depth bootstrap fit in `56.65 s` | Promote the provenance rule: share generated observables, but rerun target-specific inference and checks. |
| Generated-only adaptive block-size campaign | T006 completed 2,880 trajectories in `771.05 s`; a complete checkpointed revalidation took `40.18 s` | Reuse the loop shape—base grid, coordinate-only refinement, independent validation ensemble—while keeping paper physics case-local. |

## Harness Backlog Items

Abstract cross-paper lessons should be copied to
`PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`.

Concrete tool, checker, template, field, or workflow changes should be copied to
`PRAgent-workflow/HARNESS_BACKLOG.md`.

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| medium | Consider an explicit `figure_inset` item type | Three S4 collapse insets currently use `figure_panel` | candidate; wait for another case |
| high | Add a staggered-time observable semantics gate | `1903.05124` first feature run reversed odd/even brick-wall layers and falsified the central protection signature | copied to H098 |
| medium | Add uncertainty-label/raster consistency evidence | `1903.05124` caption says SD while plotted scale matches SE | copied to H099 |

## Prompt Or Workflow Changes

- Keep pixel tuning downstream of generated scientific data; a planned comparison is not evidence.
- Treat caption footnotes that select odd/even steps as executable model semantics, not presentation metadata.
