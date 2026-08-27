# Lessons Learned

## Case Summary

- Paper: *Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices*
- PaperID: `10.1145-3297858.3304023`
- Final status: `partial_demo_ready`
- Main reproduced targets: Fig. 3 trace, reverse traversal feature, decay trade-off feature, Table II partial reproduction.
- Main blockers: exact random initial mappings, tie-breaking rules, BKA baseline details, and some benchmark metadata remain underspecified.

## What Worked

- Algorithm papers need method cards, not only formula cards. `ALGORITHM_CARDS.md` made the SABRE pipeline inspectable before code was written.
- Benchmark corpus validation should happen before output comparison. Matching `g_ori` for 26/26 rows separated input correctness from algorithm-output mismatch.
- Mechanism figures can be validated through generated numerical experiments. Fig. 5 is a schematic, but the reverse traversal effect was checked through QFT-style circuits.
- JSON checks made partial results honest. Table II could be shown as partial without hiding exact-match counts.

## What Was Difficult

- Table-level reproduction is sensitive to implementation details not fully specified in the paper: random initial mappings, tie-breaking, exact traversal setup, and baseline implementation.
- Public benchmark inputs can be reused without using the author's implementation, but they need explicit provenance and validation.
- A figure may be a mechanism diagram while the corresponding claim is numerical. The harness needs to support "schematic source, numerical feature check" targets.

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| benchmark_input_mismatch | Table II `n` mismatch for two rows | Validate benchmark metadata against paper columns before routing. |
| unspecified_randomization | Table II exact reproduction | Record seeds, initial mappings, attempt counts, and tie-breaking rules. |
| baseline_unavailable | BKA comparison | Mark baseline-dependent targets separately from self-contained algorithm targets. |
| schematic_with_numeric_claim | Reverse traversal and decay figures | Allow schematic figures to create numeric feature checks. |
| time_tradeoff_without_metadata | Table II exact reproduction | More attempts may improve matches, but missing seed/tie-breaking metadata must remain a separate blocker. |
| premature_time_budget_request | Table II exact reproduction | Ask for larger time budgets after a first attempt provides runtime and exact-match evidence. |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| benchmark corpus validator | Many systems papers rely on benchmark tables | `PRAgent-workflow/benchmarks` |
| routing legality checker | Hardware-compliance checks recur in compiler/routing papers | `PRAgent-workflow/checks` |
| randomized-run recorder | Exact reproduction needs seeds and tie-breaking trace | `PRAgent-workflow/run_metadata` |
| table reproduction report generator | Table-level results need exact/partial/input-only status | `PRAgent-workflow/reports` |
| compute budget and attempt planner | Algorithm tables often need many randomized attempts but not necessarily more memory | `PRAgent-workflow/compute_budget` |
| post-first-attempt time budget request | Turns measured runtime into a concrete user decision | `PRAgent-workflow/time_budget` |

## Harness Backlog Items

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| high | Add benchmark corpus validator | `outputs/checks/table2_reproduction.json` | copied_to_backlog |
| high | Add input-match vs output-match separation | Table II has 26/26 `g_ori` match but partial `g_op` match | copied_to_backlog |
| medium | Add randomized run metadata capture | Table II depends on initial mappings and tie-breaking | new |
| medium | Add schematic-to-feature target support | Fig. 5 reverse traversal and decay | copied_to_backlog |

## Prompt Or Workflow Changes

- Agent should distinguish "using benchmark inputs" from "using implementation code."
- Agent should validate corpus inputs before claiming algorithm mismatch.
- Agent should state exact-match counts instead of summarizing a table as simply reproduced or failed.
- Agent should record randomization, tie-breaking, and attempt counts whenever an algorithm paper reports best-of-N results.
