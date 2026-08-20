# Method Trace

## METHOD001: five-qubit stabilizer projection

- Source: Sec. V, Eqs. (10)-(23), Appendix.
- Inputs: printed stabilizers and T-basis definition.
- Outputs: accepted/good/error weights by Hamming sector.
- Code: `src/magic_distillation/model.py::t_type_projection_table`.
- Checks: projector Hermiticity, idempotence, rank, 1/6 normalization, and
  pointwise equality to Eqs. (22)-(23).
- Status: implemented and unit tested.

## METHOD002: punctured Reed-Muller enumeration

- Source: Sec. VI, Lemmas 1-2 and Eqs. (29)-(36).
- Inputs: the 15 nonzero four-bit points and printed monomial spans.
- Outputs: exact L1/L2/L1-perp weight histograms and probability maps.
- Code: `src/magic_distillation/model.py::reed_muller_spaces` and
  `h_type_enumeration`.
- Checks: dimensions 16/1024, printed L1 enumerator, and pointwise equality to
  Eqs. (35)-(36).
- Status: implemented and unit tested.

## METHOD003: scientific runner

- Source: `run_contract.json`.
- Inputs: case-local source and `config/paper_exact.json` only.
- Outputs: frozen CSV/JSON scientific bundle; no plotting.
- Code: `scripts/run_reproduction.py`.
- Boundary: no PDF, EPS, references, author code, or author arrays.
