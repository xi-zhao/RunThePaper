# Lessons Learned

## Case Summary

- Paper: *Unidirectional Dark-to-Bright Rescue in Cavity-Coupled Quantum Transport*
- PaperID: `2608.05312`
- Final status: `numerical_feature_reproduction`, score `83.4`
- Main reproduced targets: T001–T010
- Main blockers: unpublished mean hopping/source notation/seeds/grids; missing QCLE inputs for T011

## What Worked

- Starting from the photonic-weight sum rule produced a strong invariant before any figure tuning: every ideal dark state escapes at exactly `gamma_rec`, independent of N.
- Cross-figure constraints made the omitted `t=1 meV` reconstruction falsifiable. The same value matches Table S2 endpoints, Fig. 3 fixed-rate benchmarks, and the stated QCLE peak near `g≈t`.
- Separating coherent geometry (`TransportModel`), state-changing rates (`ChannelRates`), and a cached realization (`PreparedTransport`) kept all target experiments on one physical core.
- Sparse exponential action preserved the paper's generator while making N=96 feasible on 16 GiB.
- Paired disorder realizations and data-first plotting made mechanism differences auditable.

## What Was Difficult

- The source says seeds are fixed but does not publish them; optimized site-N peaks are sensitive enough that feature agreement is stronger than pointwise agreement.
- Logical supplement numbering and source filenames are offset (`figS3_scaling_loglaw.png` is the logical Fig. S2, for example), which can silently mis-map evidence.
- Most curves are only available as raster panels. Numeric closeness must use printed anchors and feature contracts rather than pixel similarity.
- The claimed project repository is not linked in arXiv v1.
- Separate formal target launches originally overwrote `run_manifest.json`; manifest merging was added so future invocations preserve completed target groups.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Use cross-figure parameter triangulation | an omitted parameter may still be constrained by tables, fits, and captions | record every anchor and keep the run `paper_subset` |
| Judge plots through numeric feature contracts | raster similarity can hide wrong physics or penalize harmless styling | encode boundaries, endpoints, fits, and rankings in JSON checks |
| Separate model from experiment orchestration | many figures often share one small physical core | keep Hamiltonian/jumps/observables independent of paper panels |
| Pair random realizations across mechanisms | unpaired disorder adds noise to a mechanism comparison | cache realizations and reuse them for every channel |
| Treat missing scientific inputs differently from slow compute | more hardware cannot recover an omitted bath matrix | classify as `missing_source_input`, not `time_tradeoff` |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | Prevention |
| --- | --- | --- |
| guessing a paper-exact label | t/source/seeds are not all printed | force `paper_subset` caps in every artifact |
| tuning to a raster | exact curve arrays are unavailable | use independent numerics plus textual anchors |
| wrong vec convention | Lindblad Kronecker factors depend on column stacking | dense-vs-sparse regression and trace/positivity checks |
| comparing mechanisms on different disorder | optimum gaps can shift | paired seed ensembles |
| overwriting multi-invocation provenance | last target replaced prior manifest entries | merge compatible manifests by paper/profile |
| trusting raw filenames as figure numbers | supplement asset names are shifted | map logical paper IDs in `PAPER_MAP.md` |

## Recommended Practices

| Practice | When to use it | Evidence |
| --- | --- | --- |
| formula gate before numeric runs | every formula-driven paper | 7/7 equation cards open and 8 model checks pass |
| small dense oracle for a sparse solver | optimized linear propagation | max difference `3.40e-16` |
| pilot optimization, independent evaluation ensemble | expensive parameter sweeps | N=96 formal scaling completed in 347.17 s |
| interpolate phase boundaries in log-rate coordinates | log-spaced competition maps | both N=6 and N=64 boundaries match paper anchors |
| score each paper object independently | multi-figure reproduction | 10 target scores expose T005/T010 limitations |

## New Failure Modes

| Failure mode | Where it appeared | Detection |
| --- | --- | --- |
| correct trend but seed-sensitive optimum magnitude | T005 and Table S1 baseline | table MAE/max-error plus sign contract |
| reduced contour looks convincing but lacks paper uncertainty | T010 | explicit sample/grid scope field and score reduction |
| source equation exists but numerical benchmark is irreproducible | T011 QCLE | required-input ledger before implementation |
| score reason computed from the wrong metric object | initial T001 scorecard draft | generate reasons from typed claim/reference pairs and rerun scorer |

## Reusable Checks Or Tools

| Candidate | Why reusable | Suggested destination |
| --- | --- | --- |
| log-coordinate zero-boundary interpolation | common in phase diagrams | generic harness numeric-feature helper |
| sequential manifest merge | target groups are often launched separately | reproduction runner utility |
| paired-ensemble comparison contract | common stochastic simulation need | generic scientific checks |
| source-filename/logical-figure mapping check | TeX assets often use stale names | paper-map audit |

## Efficient Reproduction Implementations

| Implementation | Evidence | Scope |
| --- | --- | --- |
| cached unit-rate channel generators | all rate scans reuse one realization | generic candidate |
| sparse `expm_multiply` propagation | dense equivalence `3.40e-16`; N=96 local run | generic candidate |
| data-first target runners | 10 targets feed checks and figures from CSV | keep orchestration case-local |

## Harness Backlog Items

| Priority | Improvement | Evidence | Status |
| --- | --- | --- | --- |
| P1 | merge sequential target manifests | formal runs originally retained only the last target | implemented case-local |
| P2 | generate numeric claims from prose/table anchors | six figures lack author numeric arrays | candidate |
| P2 | validate logical figure IDs against TeX captions, not filenames | supplement asset names are offset | candidate |

## Prompt Or Workflow Changes

- Ask “is this a missing-input blocker or a compute-time tradeoff?” before recommending hardware.
- Require scorecard reasons to name the actual generated and reference metrics.
- Keep reconstructed parameters in one shared card and propagate `paper_subset` automatically to every output row.
