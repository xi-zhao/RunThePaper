# Lessons Learned

## Case Summary

- Paper: Landau and Binder (1985), J1-J2-J3 square Ising model
- PaperID: `10.1103/PhysRevB.31.5946`
- Final status: `benchmark_gold_invalid`
- Main reproduced target: exact Fig. 2
- Main blockers: incomplete historical MC contract and contradictory Fig. 15 parameter provenance

## What Worked

- Formula-first gating exposed a deterministic exact target before using the GPU.
- Explicit periodic patterns independently verified all four printed ground-state energies.
- The A100 pilot made the thermal failure measurable in 27.06 s.
- Data provenance kept the failed independent run separate from publisher pixels.

## What Was Difficult

- The benchmark record merges values and lattice ranges from different source figures.
- A first-order system can give smooth-looking but physically wrong Metropolis curves when started randomly and run briefly.
- A caption/prose disagreement cannot be repaired by spending more GPU time.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Audit parameter provenance per claim | Correct scalars may still have an invalid joint contract | map every task field to page/figure/caption |
| Check finite-size physics before styling | plausible curves can encode frozen trajectories | gate peak positions, growth laws, and hot/cold agreement |
| Preserve failed numerical data | failures reveal sampler requirements | store raw arrays, settings, and failed checks |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | Prevention |
| --- | --- | --- |
| treating a source quote as a reproducible contract | Fig. 15 has two `R` values | require one unique parameter tuple |
| short random-start Metropolis near first order | erratic peak temperatures and shrinking peaks | enhanced sampling plus phase-specific starts |
| importing a size range from another figure | frozen `L=12…32` belongs to Fig. 11 | figure-level provenance validation |

## Recommended Practices

| Practice | When to use it | Evidence |
| --- | --- | --- |
| exact lane before stochastic lane | affine/closed-form subproblems | Fig. 2 exact in sub-second runtime |
| A100 feature pilot | expensive Monte Carlo | rejected the sampler before a long run |
| terminal `benchmark_gold_invalid` | non-unique source contract | Fig. 15 caption/prose conflict |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| `source_caption_prose_parameter_conflict` | Fig. 15 `R=0.65` vs `0.75` | compare caption, adjacent prose, and task tuple |
| `cross_figure_parameter_provenance_mix` | tasks 7-10 combine Fig. 15 values with Fig. 11 sizes | require field-level source references |
| `first_order_random_start_freezing` | A100 Figs. 9-10 pilot | hot/cold starts, swap acceptance, autocorrelation, monotonic peak gate |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| caption/prose parameter conflict detector | invalidates numerical judging before compute | harness source audit |
| claim-field provenance ledger | prevents cross-figure contract mixing | benchmark audit schema |
| first-order finite-size feature gate | rejects under-equilibrated scans | Monte Carlo evaluator |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Destination |
| --- | --- | --- |
| 16-color exact interaction coloring | 4 sizes × 29 T × 8 replicas completed in 27.06 s | keep case-local until enhanced-sampling correctness is proven |
| affine-energy vectorization | exact Fig. 2 plus boundaries in sub-second time | reusable analytic pattern |

## Harness Backlog Items

| Priority | Improvement | Evidence | Status |
| --- | --- | --- | --- |
| P1 | detect caption/prose parameter conflict | Fig. 15 | recorded |
| P1 | reject cross-figure task contracts | tasks 7-10 | recorded |
| P2 | standard first-order equilibration gates | failed A100 pilot | candidate |

## Prompt Or Workflow Changes

- Require claim-field source references before paper-scale compute.
- Label a completed GPU job separately from a scientifically passed reproduction.
