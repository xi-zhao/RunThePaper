# Numerical Methods

## NUM001 — Exhaustive local algebra

- Target: `ALGEBRA_CORE`.
- Grid: all `2^8=256` three-variable `{0,π}` phase tables and all eight clause polarities.
- Solver: direct subset enumeration and inclusion-exclusion.
- Tolerance: wrapped phase error `<=1e-10`.
- Validation: exact zeta/Möbius roundtrip and one violating assignment per clause.

## NUM002 — Fig. 3 mechanism

- Targets: `FIG3C_NATIVE`, `FIG3A_ZAP`.
- Input: ordered `4 Z + 9 CZ + 6 CCZ` stream transcribed from the source panel.
- Solver: exact gate expansion plus per-qubit-order DAG scheduling.
- Validation: gate census, totals, depth, and pairwise negative controls.
- Boundary: support provenance is mixed; exact decomposed instruction order is absent.

## NUM003 — Figs. 4/5/8 eight-family proxy

- Target: `ROUTING_PROXY`; parameter match: `proxy_model`.
- Families: 3-SAT, 3-local QAOA, p-spin, 4-local hypergraph, QRAM,
  multiplier, QFT, GHZ.
- Grid: `n={6,10,20,30}`, seeds `{7,19,43,71,101}`, two strategies.
- Geometry: five-atom storage partitions, one four-atom shared zone, one
  entangler, four atoms per movement layer.
- Output: 320-row raw CSV, summary CSV, verdict JSON, fidelity/move/stage figures.
- Acceptance: six many-body advantages and exact QFT/GHZ equality.

## NUM004 — Fig. 6 scaling proxy

- Target: `ROUTING_PROXY_SCALING`.
- Families: 3-SAT, p-spin, QRAM; sizes `{20,40,60,80,100}`; seed 19.
- Timing: median of five local Apple M4 compile-plus-route repetitions.
- Output: duration/timing CSV, verdict JSON, two-row scaling figure.
- Boundary: local timings are not author timings.

## NUM005 — Fig. 7 sensitivity proxy

- Target: `ROUTING_PROXY_SENSITIVITY`.
- Fixed routes: 3-SAT, p-spin, QRAM at 30 qubits, seed 19.
- Grid: 41x41 points over `p3,p4 in [0,0.2]`; 5,043 rows.
- Method: hold routing, movement, idle, and decomposed ZAP exposure fixed while
  replacing native three-/four-body fidelities.
- Acceptance: 3-SAT is p4-independent; p-spin/QRAM depend on both errors;
  Table-I representative point favors native.
- Partial result: none of the three proxy surfaces crosses break-even. The
  result is not tuned because the route-residency model is intentionally simple.

## Efficiency And Reuse

All runs fit comfortably on the local M4/16 GiB machine. The scientific
bottleneck is missing author route state, not compute. Case-specific generators
and geometry remain local; only the target/verdict control pattern is generic.
