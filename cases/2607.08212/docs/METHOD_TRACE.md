# Method Trace

## METHOD001 — Local Möbius frontend

- Source: Algorithm 1 lines 2-8; Eqs. (6)-(14).
- Core object: a sparse phase-hypergraph support map `(S, theta_S)`.
- State transition: local phase table -> Möbius inverse -> merged/wrapped supports.
- Invariants: zeta reconstruction is exact modulo `2π`; global/zero terms are discarded.
- Code: `src/mobius_compiler.py`.
- Evidence: 256 exhaustive roundtrips and eight literal-polarity checks.
- Status: executable and verified.

## METHOD002 — Fig. 3 gate accounting

- Source: Fig. 3 caption, Sec. III.B, and vector source panel.
- Core object: ordered native gate stream.
- Transition: each CCZ -> exact six-CNOT/seven-phase parity gadget -> each
  CNOT lowered to `H-CZ-H` -> per-qubit-order ASAP schedule.
- Evidence: native `19/12`; decomposed 163-gate census exact; generated depth
  `121` versus paper `128`.
- Code: `src/mobius_compiler.py`, `scripts/run_feature_reproduction.py`.
- Remaining gap: the paper's within-block ordering and concrete six clauses.

## METHOD003 — Routed proxy campaign

- Source: Algorithm 1 lines 23-27, Secs. IV-V, Eq. (23), and Table I.
- Status: `reconstructed_proxy`, explicitly approved and expanded by the user.
- Core object: a logical support stream plus explicit geometry/scheduler contract.
- Families: synthetic 3-SAT, 3-local QAOA, p-spin, 4-local hypergraph,
  QRAM, multiplier, QFT, and GHZ.
- Native transition: retain supports of degree 3-4.
- ZAP transition: three-body terms use the fixed CCZ gadget; four-body terms use
  an exact Gray-code parity-phase census before `CNOT -> H-CZ-H` lowering.
- Router: per-qubit-order shared-zone ASAP scheduling with one entangler and
  declared movement throughput; independent entanglers may fill earlier gaps.
- Metric: Eq. (23) evaluated in log space with Table-I values.

### Executed targets

1. Figs. 4/5/8 proxy: eight families, four sizes, five seeds, 320 route rows.
2. Fig. 6 proxy: 3-SAT/p-spin/QRAM, 20-100 qubits, five local timing repeats.
3. Fig. 7 proxy: fixed `n=30` routes, 41x41 `(p3,p4)` grid, 5,043 rows.

### Validation

- All six many-body families improve proxy log fidelity.
- QFT/GHZ native and ZAP streams match exactly.
- Native duration and local compile-plus-route time are lower at every Fig. 6 point.
- Fig. 7 degree dependence and representative Table-I point pass.
- Fig. 7 break-even contours do not appear; this is a retained model mismatch.

Code: `src/proxy_router.py`, `scripts/run_proxy_*.py`. Contract:
`config/routing_benchmark_contract.json`.

## Agent state adapter

`repro_adapter.json` consumes `proxy_campaign_result.json`, which aggregates all
three proxy targets. The next action is `AuthorArtifactStage`: local proxy work
is exhausted; exact Figs. 4-8 require author artifacts.
