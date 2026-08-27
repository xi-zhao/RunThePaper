# Target Ledger

## T001: Paper SWAP Example

- Scope: algorithm trace.
- Status: feature_match / passed.
- Source: Fig. 3 and text in Problem Analysis.
- Goal: route the six-CNOT 4-qubit example on the square coupling graph.
- Acceptance:
  - output circuit is hardware-compliant;
  - exactly one SWAP is sufficient for the paper's default mapping;
  - additional CNOT-equivalent count is 3.
- Evidence:
  - `outputs/checks/paper_swap_example.json`
  - `outputs/data/paper_swap_example_ops.csv`
  - `outputs/figures/paper_swap_example_trace.png`
- Result:
  - original two-qubit gates: 6;
  - inserted SWAPs: 1;
  - additional CNOT-equivalent gates: 3;
  - output depth: 8.

## T002: Core SABRE Sanity Benchmarks

- Scope: algorithm reproduction.
- Status: feature_match / passed.
- Source: Algorithm 1 and heuristic sections.
- Inputs:
  - synthetic Ising/path circuits;
  - QFT-style circuits generated locally.
- Acceptance:
  - all routed circuits are hardware-compliant;
  - reverse traversal improves or matches first traversal on representative
    cases;
  - routing terminates without using exhaustive mapping search.
- Evidence:
  - `outputs/checks/core_benchmarks.json`
  - `outputs/data/core_benchmarks.csv`
  - `outputs/figures/core_benchmarks_qft.png`
- Result:
  - topology-aligned Ising path requires 0 inserted SWAPs;
  - QFT-6 first traversal: 21 additional CNOT-equivalent gates, depth 34;
  - QFT-6 forward-backward-forward: 9 additional CNOT-equivalent gates, depth 31;
  - QFT-8 first traversal: 42 additional CNOT-equivalent gates, depth 70;
  - QFT-8 forward-backward-forward: 21 additional CNOT-equivalent gates, depth 57;
  - QFT-10 first traversal: 54 additional CNOT-equivalent gates, depth 109;
  - QFT-10 forward-backward-forward: 36 additional CNOT-equivalent gates, depth 92.

## T003: Decay Trade-Off

- Scope: numeric reproduction.
- Status: feature_match / passed_first_pass.
- Source: Fig. 8 and decay heuristic section.
- Goal: sweep `delta` values and plot normalized gate count vs normalized depth.
- Acceptance:
  - result shows a measurable gate/depth trade-off;
  - every routed circuit is hardware-compliant;
  - data is emitted as CSV and plot.
- Evidence:
  - `outputs/checks/decay_tradeoff.json`
  - `outputs/data/decay_tradeoff.csv`
  - `outputs/figures/decay_tradeoff.png`
- Result:
  - no-decay baseline: 195 additional CNOT-equivalent gates, depth 160;
  - decay sweep creates a shallower point: 198 additional CNOT-equivalent gates,
    depth 142;
  - all routed circuits are hardware-compliant.
- Limitation:
  - This reproduces the decay trade-off behavior on a seeded local circuit. It
    is not a claim of exact Fig. 8 value reproduction because the original
    benchmark corpus is not included in the paper source.

## T004: Table II Comparison Skeleton

- Scope: numeric reproduction.
- Status: planned_large_scale / partial_corpus_imported.
- Evidence:
  - `references/benchmark_sources.md`
  - `references/table2_expected.csv`
  - `outputs/checks/table2_reproduction.json`
  - `outputs/data/table2_reproduction.csv`
  - `outputs/data/table2_attempts.csv`
  - `outputs/figures/table2_gop_comparison.png`
- Result:
  - imported all 26 Table II benchmark QASM inputs;
  - validated `g_ori` against the paper for 26/26 rows;
  - validated qubit count `n` for 24/26 rows;
  - all 26 routed outputs are hardware-compliant;
  - 2026-06-18 A100 rerun scale: 1000 attempts per row, seed 0, 16 workers;
  - exact `g_op` match against Table II for 7/26 rows;
  - exact `g_la` match against Table II for 0/26 rows;
  - 19/26 rows produce lower `g_op` than the table value, which means exact
    value matching depends on the paper's search policy, not only legality.
- Current blockers for exact Table II reproduction:
  - the exact random initial mappings used in the paper are not specified;
  - `sym6_145` and `sym9_193` have QASM/table qubit-count mismatches;
  - the paper's implementation-level tie-breaking and traversal details are
    still not fully determined from text alone;
  - BKA exact reproduction still requires a separate baseline implementation.
- Large-scale plan:
  - `PLANNED_LARGE_SCALE_RUNS.md`
  - `config/table2_exact_reproduction_recommended.yaml`
