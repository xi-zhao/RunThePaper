# Consistency Report

## Consistent Features

| Feature | Paper expectation | Local result | Status |
| --- | --- | --- | --- |
| Paper SWAP example | Six two-qubit gates route with one SWAP in the paper example. | One SWAP, three additional CNOT-equivalent gates, depth 8. | consistent |
| Hardware-compliant routing | Routed circuits must respect the coupling graph. | All local outputs in the refreshed run are hardware-compliant. | consistent |
| Reverse traversal benefit | Forward-backward-forward traversal should improve the initial mapping. | QFT-style benchmarks improve or match gate count and depth. | consistent |
| Decay trade-off | Decay heuristic trades gate count for depth. | Local sweep finds a shallower point at slightly higher additional CNOT count. | consistent |
| Table II input validation | Benchmark inputs should match paper metadata. | `g_ori` matches 26/26 rows; `n` matches 24/26 rows. | mostly_consistent |

## Partial Or Not Exact

| Item | Reason |
| --- | --- |
| Table II `g_op` exact values | Exact seed, initial mapping, tie-breaking, and traversal details are not fully specified. |
| Table II `g_la` / BKA baseline | Requires a separate baseline implementation or validated baseline outputs. |
| Two benchmark qubit counts | `sym6_145` and `sym9_193` have QASM/table `n` mismatches. |

## What The Case Proves

The case proves the reconstructed SABRE pipeline is executable, hardware-compliant, and reproduces the paper's qualitative algorithmic behavior. It also separates input-corpus validation from exact output matching.

## What It Does Not Prove

It does not yet prove exact Table II reproduction. That target is now recorded as `planned_large_scale` with a batch-style attempt plan.
