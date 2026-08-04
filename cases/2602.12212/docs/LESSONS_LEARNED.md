# Lessons Learned

## Case Summary

- Paper: *Quantum-Coherent Thermodynamics: Leaf Typicality via
  Minimum-Variance Foliation*
- PaperID: `2602.12212`
- Final status: `numerical_feature_reproduction`
- Main reproduced targets: Main Figs. 1–2 and Figs. S1–S6
- Main blocker: author numerical arrays are unavailable

## What Worked

- Treating `MinimumVarianceEnsemble` as the single domain object kept every
  figure on the same verified variational rule.
- The thermal hyperbolic-secant form avoided numerical instability from tiny
  Gibbs eigenvalues.
- Pauli strings implemented as permutations avoided dense local-operator
  storage and made 12-observable sweeps cheap.
- Group/size atomic shards made it safe to interrupt an obsolete L=12 run and
  resume with corrected benchmark coverage.
- A source-figure sensitivity canary resolved the otherwise undocumented
  periodic boundary and shell-centering choices.

## What Was Difficult

- The paper supplies Wolfram-rendered figures and TeX, but no numerical code or
  data.
- The exact integer shell rule, edge handling, site convention, and confidence
  interval algorithm are omitted.
- A low-temperature representative with population \(6\times10^{-24}\)
  amplified an irrelevant all-state energy error while density/QFI identities
  remained accurate.
- The documented A100 JupyterHub endpoint was unreachable.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Stable thermal algebra belongs in the core model | Direct density-eigenvalue formulas can underflow even when the physical result is well conditioned | Prefer partition-function-free forms such as `sech(beta*deltaE/2)` and prove equivalence in tests |
| Tiny-population states need weighted diagnostics | A max error can be dominated by states that carry no numerical weight | Report all-state max, active-population max, and population-weighted RMS together |
| Figure captions can hide benchmark curves | A script may reproduce the main solid line while silently omitting dashed/dotted controls | Encode every line family in the figure coverage/target contract before large runs |
| Remote acceleration must not become a false blocker | Exact local execution may already fit the bounded budget | Measure one paper-scale shard before declaring external hardware mandatory |
| Source-only comparisons need conservative scoring | Visual agreement is not a pointwise numerical reference | Preserve side-by-side evidence and accept the score cap until digitized/author data exist |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Recomputing correct physics for a missing line family | Initial supplemental shards lacked the commuting benchmark | Make line-family coverage machine-readable before production |
| Calling every floating-point outlier a formula failure | Tiny \(p_i\) caused a \(10^{-5}\)-scale all-state energy discrepancy at a smaller canary | Gate active/weighted errors while preserving the all-state value for audit |
| Assuming documented hardware is reachable | A100 details were present, but the endpoint rejected both browser and HTTP access | Test the access path early and retain an exact local fallback |
| Using pixel metrics on independent layouts | Wolfram and Matplotlib panels are not registered | Compare physical feature contracts and structured data, not SSIM |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| `tiny_population_false_formula_failure` | Low-temperature minimum-variance representatives | Save active-population max and weighted RMS beside the unconditional max |
| `visible_benchmark_family_omitted` | Initial S1–S4 campaign data | Compare the target ledger with every solid/dashed/dotted line family before production |
| `documented_accelerator_unreachable` | A100 JupyterHub entry | Test browser and direct-network reachability before treating the hardware profile as executable |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Formula gate before figure generation | Any reconstructed scientific method | 9/9 formula cards and per-shard QFI identities passed |
| Atomic shard writes | Dense runs with independent sizes/groups | Interrupted L=12 output did not corrupt passed main data |
| Full final uncertainty sample | When the paper's confidence object is small enough | All 214 delta-shell states cost only 7.44 s of evolution |
| Separate source and generated provenance | Whenever source figures are locally available | Comparison boards never feed generated CSVs |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| population-aware representative-energy invariant | Applies to ill-conditioned ensemble decompositions | promote after a second case |
| Pauli permutation application | General exact-diagonalization primitive | case-local until another spin-chain case needs it |
| aggregate shard manifest | Prevents the last resumable invocation from hiding earlier completed groups | harness campaign pattern |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote |
| --- | --- | --- |
| Eigensystem reuse across three beta values | L=12 standard group completed in about 5 minutes locally | keep case-local orchestration |
| Batched shell-state evolution | 214-state, 61-time evolution took 7.44 s after eigensystems | keep dynamics helper case-local |
| Sparse Hamiltonian build + dense `eigh` | exact \(d=4096\) result within memory | standard pattern |

## Harness Backlog Items

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| medium | Add a generic line-family coverage ledger beneath each figure target | Supplemental dashed benchmarks were initially omitted | proposed |
| low | Add standard population-aware invariant fields | Tiny-population numerical amplification is predictable | proposed |

## Prompt Or Workflow Changes

- Ask for every visible line family—not only every figure—during the target
  coverage pass.
- Run a paper-scale timing probe locally before classifying external compute as
  mandatory.
- When confidence-band metadata are omitted, separate exact trajectory coverage
  from interval-estimator reconstruction in both checks and scorecards.
