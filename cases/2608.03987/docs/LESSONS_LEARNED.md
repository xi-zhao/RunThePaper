# Lessons Learned

## Case Summary

- Paper: *Realified tensor networks: quantum circuit simulation on real-valued
  matrix accelerators*
- PaperID: `2608.03987`
- Final status: `completed_with_differences`
- Main targets: Figures 8 and 9 at all 67 circuits
- Blockers: none; the remaining gap is an empirical optimizer mismatch

## What Worked

- The tensor hypergraph is the right core model: one lowering path supports
  random, Clifford+T, QAOA, and VQE circuits.
- Integer bit masks make hyperedge boundaries exact and NNI updates local.
- An exact dynamic-programming optimizer for tiny networks catches cost-model
  and tree-update errors before large stochastic runs.
- Per-circuit configuration/topology hashes make a long campaign safely
  resumable and deterministic.
- Separating primary clean-room evidence from post-hoc author comparison keeps
  provenance clear.

## What Was Difficult

- Qsim's `sqrt(Y)` is real while `sqrt(X)` is complex; gate names alone are an
  unsafe proxy for structural complexity.
- Expectation networks require an explicit rank-2 middle operator on every
  wire, including identities, to separate ket and bra topology correctly.
- Figure 9's overhead denominator changes with the tree. Reporting only
  `|o_convert-o_full|/o_full` can obscure actual cost changes, so the run also
  audits `|C_convert-C_full|/C_full`.
- Stochastic tree search is part of the scientific result, not a disposable
  implementation detail: a different optimizer reproduced the law but changed
  nine threshold classifications.

## Generalized Experience

| Lesson | Why it matters | Recommendation |
| --- | --- | --- |
| Freeze an explicit source boundary | A reproduction can silently become an author-code rerun | Audit every input payload and distinguish primary from post-hoc data. |
| Test topology before optimization | Parser mistakes can imitate optimizer disagreement | Compare index sets and tensor classes independently on the full corpus. |
| Keep exact and empirical claims separate | Algebraic identities and search-budget observations have different failure semantics | Use separate gates and allow empirical differences to survive plotting. |
| Audit the underlying objective | Ratios with per-result denominators can be misleading | Report both normalized metric and absolute/relative objective gap. |
| Store full stochastic outputs | Aggregate curves cannot establish reproducibility | Save seeds, configuration hashes, tree child pairs, and tree hashes. |

## New Failure Modes

| Failure mode | Where it appeared | Detection |
| --- | --- | --- |
| Optimizer-equivalence assumption | Figure 9 | Compare threshold labels circuit by circuit under an independent search. |
| Denominator-induced gap distortion | VQE YY circuit | Audit real cost and overhead gap together. |
| Concurrent manifest race | Parallel full campaign | Regenerate one final all-skip manifest after every circuit checkpoint exists. |

## Reusable Checks Or Tools

| Candidate | Value | Suggested destination |
| --- | --- | --- |
| ZIP payload source-boundary audit | Proves which artifact classes were actually consumed | paper-reproduction harness |
| Exact small-tree DP oracle | Verifies arbitrary contraction cost models | tensor-network helper library |
| Python multi-format figure QA | Checks PDF dimensions/fonts, editable SVG text, dpi, opacity, and TIFF compression | nature-figure workflow |
