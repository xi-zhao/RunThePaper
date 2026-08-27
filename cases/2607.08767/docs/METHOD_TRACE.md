# Method Trace

Use this file for algorithmic or systems papers where the key reproduction
object is a method rather than a formula.

## Method Cards

### METHOD001

- Source: Section IV.A, Eq. (9), Eq. (10), Fig. 5(a).
- Role: Compare an exact coherent channel with its Pauli-twirled approximation
  on one explicit repetition-memory circuit.
- Inputs: `theta`, code distance, stabilizer rounds, shots, seed.
- Outputs: JSON verdict, CSV observations, comparison figure.
- Algorithm steps:
  1. Encode logical `|+>` as a GHZ state.
  2. At each round, insert Eq. (9) or an identity marked for Eq. (10).
  3. Measure adjacent ZZ stabilizers with ideal ancillas.
  4. Measure all data qubits in X and classify odd parity as logical failure.
  5. Compute Clopper-Pearson 95% intervals.
  6. Compare with Fig. 5(a) paper values without tuning the circuit.
- Parameters: `theta=0.05`, `distance=3`, `rounds=3`, `5000/200000` shots.
- Code pointer: `scripts/run_fig5a_proxy.py`.
- Checks: Eq. (9) unitarity, Eq. (10) normalization, deterministic seed,
  coherent logical error greater than twirled logical error.
- Status: proxy executed; method direction reproduced, full-state paper value not reproduced.
- Open questions: Exact Plaquette-generated circuit locations, Clifford-frame
  convention, decoder graph, and whether the error is attached to data,
  ancilla, idle, or round-boundary locations.

### Agent state adapter

`repro_adapter.json` maps the durable Fig. 5(a) verdict into the
generic `RunState` interface.  A failed full-state metric emits
`paper_metric_verdict_stop`, allowing the active lesson to require failure
attribution before any larger simulation.  The existing reusable
`FailureAttributionStage` still contains 2604 distance-metric assumptions, so
this case permits planning/preview but does not authorize executing that stage.
The bounded operator was run with `--no-run-stage`, leaving the durable state at
`stage_requested` with no model call, training, or remote execution.
