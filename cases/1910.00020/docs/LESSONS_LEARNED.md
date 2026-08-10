# Lessons Learned

1. Phase-free tableaux are a deep simplification, not a shortcut. For stabilizer entropies, signs and measurement outcomes can be removed exactly, provided the scope is stated and tested with Bell/product cases.
2. A visually plausible curve can still encode the wrong channel. T003 exposed a reproduction defect: omitting measurements outside the retained record is not equivalent to performing them and marginalizing their outcomes. The correct mixed-stabilizer dephasing channel is derivable from the paper's physical protocol.
3. Critical-exponent figures are sampling-hungry. Small systems readily recover the transition direction and approximate crossing, but surface/correlation exponents drift and curves remain jagged.
4. Pixel similarity must follow data freeze. Here it correctly reveals large plot-level differences (46.61 foreground mean) without being allowed to change trajectories or physics.
5. GPU availability is not automatically useful. Small GF(2) tableau operations are better served by packed CPU parallelism unless many trajectories are batched.

Reusable harness opportunity: add a stabilizer-specific evidence helper that records whether phase omission is exact for the declared observables, and add an explicit `decoder_equivalence` gate for partial-record measurement studies.

## New Failure Modes

- A partial-record decoder can look visually correct while computing a different conditional channel. Require an explicit method-equivalence declaration before scoring it as paper-exact.
- Small-trajectory critical curves can pass monotonicity and positivity checks while producing biased exponent fits. Require both sample-count and size-doubling checks for precision claims.

## Reusable Checks Or Tools

- `phase_free_stabilizer_scope_check`: verifies that every declared observable is invariant to omitted Pauli phases.
- `decoder_equivalence_gate`: requires physical measurements outside a retained record to remain in the channel and verifies unknown-outcome marginalization independently.
