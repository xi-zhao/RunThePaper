# Lessons Learned

## New Failure Modes

- Large-scale simulation papers can have correct formulas but infeasible local full-size targets. The harness needs a resource-feasibility gate before claiming exact reproduction.
- Direct statevector memory can be a hard blocker, not a time-tradeoff. For 53-qubit circuits, the right next step is tensor-network assets or author data, not simply waiting longer locally.
- arXiv and journal versions can differ substantially. This case has a 6-page PRL version and a 9-page arXiv version with more figures and source assets.
- Source figures can exist without raw plotting data. The harness should treat original figure PDFs as visual references, not as numerical ground truth.
- Complexity tables mix measured timing, extrapolated timing, and theoretical operation counts. They need a table-specific consistency report.

## Reusable Checks Or Tools

- Add an arXiv source renderer that extracts figure PDFs and converts them into `internal-paper-reference/`.
- Add a Porter-Thomas feature checker for random-circuit papers: histogram slope, XEB near zero for full batch, post-selection curve, and conditional normalization.
- Add a large-scale feasibility classifier with statuses such as `feature_reproduced`, `author_data_validated`, `exact_large_scale_blocked`, and `hardware_rerun_required`.
- Add a memory-vs-time classification so the agent knows when to offer longer local runs and when to recommend external hardware immediately.
- Add a table complexity checker that can verify relationships like `T_head = #subtasks * T_sub` and `T_tail << T_head`.

## Harness Backlog Updates

copied_to_backlog: `H011`, `H012`, `H013`
copied_to_backlog: `H019`

## Case-Specific Takeaway

For quantum circuit simulation papers, the agent should first reproduce the probability logic on a small circuit. Only after that should it attempt to ingest real benchmark circuits or author-released probability data.
