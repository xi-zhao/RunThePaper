# Lessons Learned

## Case Summary

- Paper: Dissipative Phase Transition in the Two-Photon Dicke Model
- PaperID: 2412.14271 / DOI 10.1103/mz92-6l9g
- Final status: partial feature reproduction
- Main reproduced targets: Fig. 2, Fig. 3, Fig. 4, Fig. S1, Fig. S2,
  reduced Fig. S5, and the parity supplement
- Explicit uncovered items: formal Fig. S3 and formal Fig. S4; their panel
  inventories, observables, and parameters are unavailable
- Other fidelity blockers: paper-scale trajectory counts and fresh-context
  review remain pending

## What Worked

- The analytic and quantum lanes shared one explicit Hamiltonian/Lindblad model
  but produced independent observables and checks.
- Trace, positivity, cutoff-tail, Wigner-normalization, Z4, and parity checks
  caught scientific failures that a visually plausible plot would hide.
- Sparse shift-invert around zero recovered the two-dimensional Liouvillian
  kernel in 14.38 seconds; asking for largest-real-part modes did not.
- Freezing and hashing arrays before opening source figures kept numerical
  inference separate from RenderContract tuning.

## What Was Difficult

- Quantum-trajectory cost varies strongly with photon cutoff and coupling; the
  N=15, M=240 point cost about 18.3 seconds per trajectory locally.
- Reduced ensembles reproduce phase-space structure but do not restore the
  paper's Z4 symmetry accurately; residuals remained 0.13-0.62.
- The fixed point visually matching the paper's lower plotted branch is stable
  under the printed Jacobian, contradicting its unstable label.
- QuTiP imports Matplotlib. The isolation harness replaced a declared font
  cache and accidentally triggered forbidden system font-discovery subprocesses.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Branch identity and stability are separate gates | A root can match a plotted ordinate while carrying the opposite stability label | Substitute each root into the equations, then diagonalize the Jacobian before assigning a plotted branch |
| Dependency caches are declared scientific-run inputs | Rebuilding caches can invoke hidden filesystem or subprocess behavior | Resolve declared cache paths inside the isolated bundle and hash their contents |
| Symmetry residual is a convergence observable | A recognizable Wigner shape can still be statistically underconverged | Record symmetry residuals beside visual output and trajectory count |
| Near-zero spectral questions need targeted solvers | Generic extremal-eigenvalue requests can be orders of magnitude slower | Use shift-invert near a declared nonzero numerical shift and verify residuals |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| White-background pixel inflation | Full pixel similarity was 90.41/100 while foreground similarity was 46.72/100 | Always publish both full-canvas and foreground-union metrics |
| Treating finite-time QT as ED | Fig. 2's cutoff instability was reproduced by trajectories, not the paper's steady-state ED | Keep method variant in target fidelity and never mark paper-exact |
| Long monolithic trajectory runs | An interrupted run had no reusable job-level checkpoint | Save each parameter/seed job atomically and resume from a manifest |
| Source-version drift | The formal paper refers to S3-S5, while accessible v1 material has a different supplement inventory | Track figure identity and parameters per source version |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Analytic landmark before simulation | Open-system phase transitions | The exact threshold lambda_c=0.509901951 anchored all later scans |
| Density-matrix invariants before rendering | Quantum trajectories and master equations | Trace error <=5.6e-15 and cutoff tail <=2.1e-9 established numerical validity |
| Freeze arrays before RenderContract | Any pixel-scored reproduction | All comparison boards refer to four recorded data hashes |
| Distinguish artifact validity from lifecycle completion | Any partial paper reproduction | Seven valid targets coexist with one blocked target and reduced sampling |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Declared cache silently overwritten | isolated QuTiP import | Test environment resolution and forbid cache paths outside the staged bundle |
| Stability-label/branch mismatch | Fig. S2 / Fig. 3 analytic branch | Match root value, residual, and Jacobian eigenvalues as a three-part branch identity |
| Symmetry hidden by ensemble noise | Fig. 4 Wigner functions | Require a target-specific Z4 residual threshold before paper-exact status |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| Declared-cache isolation test | Scientific libraries often initialize font/JIT/model caches | isolated runner tests |
| Symmetry-residual check | Applies to Wigner functions, order parameters, and lattice fields | generic scientific-check schema |
| Job-level trajectory checkpoint manifest | Long parameter/seed ensembles are naturally decomposable | harness runner backlog |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| Sparse Liouvillian shift-invert | N=4, M=50 kernel completed in 14.38 s after a >10 min extremal attempt | promote solver guidance, keep model code local |
| Shared generated photon density matrix | Fock and Wigner panels reuse one frozen state | promote immutable-artifact pattern |
| Cumulative trajectory summaries | 4/10/final convergence came from one ensemble | promote as trajectory-runner option |

## Harness Backlog Items

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| P0 | Preserve declared dependency caches inside isolated bundles | Matplotlib font discovery caused false isolation failures | fixed and tested |
| P1 | Add per-job checkpoint/resume for ensemble sweeps | 9-minute run contains 18 independently restartable jobs | proposed |
| P1 | Add branch-identity/stability audit schema | Plotted root and positive-eigenvalue spectrum belong to different fixed-point branches | implemented for T005 |
| P2 | Add symmetry-residual scientific check | Z4 residual reveals low trajectory counts | proposed |

## Prompt Or Workflow Changes

- Ask first for the cheapest falsifiable analytic landmark, then run a one-job
  isolation smoke, then a reduced feature campaign, and only then request a
  measured paper-scale time budget.
- Never let a RenderContract score upgrade method fidelity, sampling fidelity,
  or paper coverage.
