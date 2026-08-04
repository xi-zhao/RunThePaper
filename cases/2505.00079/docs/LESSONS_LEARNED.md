# Lessons learned — idx56

## What worked

- The source archive exposed exact algorithm and sample-count contracts.
- A local-action-versus-full-action test caught the most important scientific
  implementation risk before any expensive sampling.
- Reporting raw and symmetry-augmented Q separately resolved an apparent Z4
  discrepancy without manipulating the Markov chain.
- Hot/cold Z7 smoke exposed metastability and selected the physically consistent
  cold result at high beta for the baseline.

## General lessons

| Lesson | Why it matters | Future practice |
| --- | --- | --- |
| Audit directional language, not only scalars | frozen gold reversed the central defect mechanism | compare every qualitative trend directly with primary text |
| Plot conventions can change a statistic | Z_N orbit augmentation makes Q exactly zero | encode transformations as named tested functions and retain raw values |
| Matching sample count is not parameter exactness | burn-in and chain count are absent | declare `paper_subset` and list every missing run parameter |
| Critical observables need a failure gate | a plausible-looking smoke produced chi far below target | make numeric mismatch explicit before scaling |
| GPU value requires batch semantics | one tiny L^4 lattice underuses A100 | batch independent chains and disclose aggregation |

## New Failure Modes

- `benchmark_direction_reversed`: gold qualitative trend contradicts source and
  independent data.
- `symmetry_augmentation_underspecified`: a benchmark statistic assumes a
  plotting augmentation without saying so.
- `paper_total_count_chain_structure_unknown`: total samples match but the
  paper's number of chains is not reported.
- `critical_smoke_false_negative`: correct kernel misses susceptibility peak
  because decorrelation/sample count is far below source.

## Reusable Checks Or Tools

- Complete finite-group orbit augmentation and raw/augmented paired metrics.
- Resumable structured-array runner with RNG/link checkpoints and progress JSONL.
- CPU scientific oracle plus batched Torch backend cross-check.

These remain case-local until another paper demonstrates the same abstraction.
