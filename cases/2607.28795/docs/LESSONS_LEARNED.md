# Lessons Learned

Use this file after each reproduction pass. The goal is to extract reusable
lessons from one paper and turn them into better Agent and harness behavior for
the next paper.

## Case Summary

- Paper: High-rate qLDPC processors
- PaperID: 2607.28795
- Final status: bounded numerical feature reproduction; lifecycle incomplete
- Main reproduced targets: exact Tables V and X, reduced Algorithm-1 benchmark
- Main blockers: literal Table-XIII construction discrepancy, missing optimized
  schedule/layout inputs, and intentionally skipped paper-scale stochastic work

## What Worked

- Reconstructing the finite-group action at the paper-cited GAP/SmallGrp
  versions made the code properties directly falsifiable.
- Freezing numerical hashes before transcribing reported scalars prevented the
  comparison lane from influencing generation.
- A known-code control (Steane distance 3) tested Algorithm 1 independently of
  the paper's unavailable production benchmark.
- The source-aware style contract and source-blind render run kept visual
  tuning separate from physical data.

## What Was Difficult

- GAP's `Elements(G)` position is an implementation-level convention that can
  be decisive even when the group ID and package version are printed.
- Matplotlib tried to scan user fonts and launch a child process inside the
  renderer; the strict sandbox correctly rejected it.
- Fig. 8 does not disclose enough benchmark metadata to recreate a comparable
  CPU baseline, even before considering its roughly `10^12` trials.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Version pinning is necessary but not sufficient | Enumeration/order conventions can change a mathematical construction | Record explicit semantic mappings and test pivots/invariants before accepting table values |
| Reported outputs belong after the freeze | Otherwise optimization can leak target answers into generation | Bind comparison assets to a prior numerical attestation and frozen-manifest hash |
| Pixel comparison requires the same scientific object | A similar layout cannot validate different sizes, trials, or hardware | Mark pixel status not applicable for reduced-scale targets and publish only a labelled feature-audit board |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Treating printed group indices as self-explanatory | mitten-300 pivot blocks became singular | Add a group-index semantic card and a pivot-rank preflight |
| Relaxing isolation to make plotting work | Matplotlib font discovery attempted undeclared reads/processes | Freeze font metadata as an explicit renderer input |
| Comparing projected runtimes as paper values | Local RREF and paper QDistRnd are not equivalent baselines | State baseline identity and hardware as part of the parameter contract |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Known-code algorithm control | New coding-theory search/decoder implementations | Steane control recovered distance 3 |
| Exact GF(2) invariants before performance | qLDPC construction or decoder benchmarks | CSS commutation, rank, rate, and pivot tests exposed T001 |
| Frozen font cache | Strict isolated scientific rendering | render v2 passed with 0 denied events after render v1 failed |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| `group_element_mapping_ambiguous` | T001 / Table XIII | Recompute pivot ranks and canonical weights from an explicit element-position map |
| `renderer_font_discovery_escape` | failed render v1 | Treat font metadata as a declared immutable artifact |
| `benchmark_baseline_identity_missing` | T003 / Fig. 8 | Require baseline algorithm, seeds, matrix corpus, hardware, and trial definition before `paper_exact` |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| GAP table exporter with version metadata | Reuses exact finite-group multiplication tables without author code | case-local until another qLDPC paper needs it |
| Post-run non-scoring audit board | Shows the paper panel without pretending reduced runs are pixel comparable | harness comparison helper |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| Packed NumPy GF(2) elimination and null-space routines | all bounded targets finish in 0.660 s attested wall time | keep case-local pending broader benchmarks |
| Frozen SmallGrp multiplication tables | all eight constructions rerun without invoking GAP in the isolated runner | reusable pattern; table remains case-local |

## Harness Backlog Items

Abstract cross-paper lessons should be copied to
`PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`.

Concrete tool, checker, template, field, or workflow changes should be copied to
`PRAgent-workflow/HARNESS_BACKLOG.md`.

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| medium | Add a standard non-scoring, reduced-scale audit-board mode | T003 needs source context but must not receive a pixel score | candidate |
| medium | Document font-cache freezing in isolated render templates | strict render v1 failed solely on font discovery | candidate |

## Prompt Or Workflow Changes

- Require an explicit scientific-object equivalence decision before opening a
  pixel-scoring loop.
- For finite-group papers, make enumeration semantics a first-class formula
  assumption rather than a hidden preprocessing detail.
