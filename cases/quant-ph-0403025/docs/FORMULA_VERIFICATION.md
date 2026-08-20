# Formula Verification

Machine-readable result: `outputs/checks/formula_verification.json`.

## Gate Summary

| Formula | Role | Gate | Independent check |
| --- | --- | --- | --- |
| EQ001 | fidelity/error/polarization conversion | verified | Bloch-overlap identity |
| EQ002 | five-copy T input distribution | verified | 32 error probabilities normalize to one |
| EQ003 | five-qubit stabilizer projector | verified | Hermitian, idempotent, rank two, normalization `1/6` |
| EQ004 | T success probability | verified | explicit projector enumeration; endpoints `1/6`, `1/16` |
| EQ005 | T output error | verified | explicit projector enumeration; exact fixed point; coefficient `5` |
| EQ006 | punctured Reed–Muller spaces | verified | enumerate 16 `L1` and 1024 `L2` codewords |
| EQ007 | H success/output maps | verified | independent weight enumerator; fixed point; coefficient `35` |
| EQ008 | recursive distillation exponents | verified | logarithmic identities and finite recurrence |
| EQ009 | circuit-level ancilla scaling | verified | symbolic composition and printed rounding |

All 9 formula cards are numerically open. No target is fed by a formula marked source-only, reconstructed, unclear or blocked.

## Boundary

The source EPS/PDF curves are excluded from formula verification and never provide numeric samples. They enter only after the scientific arrays are frozen, through `config/render_contract.json`.
