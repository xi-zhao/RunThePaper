# Method Trace

This frozen Trial is formula-based, not algorithm-based. All executable
dependencies are captured in `EQUATION_CARDS.json` and
`DERIVATION_TRACE.md`; `method_traces` is intentionally empty.

The only numerical method is deterministic evaluation of a \(4\times4\)
density-matrix trace on a fixed angle grid, followed by direct plotting. There
is no optimizer, fit, random seed, experimental-data ingestion, or iterative
solver.
