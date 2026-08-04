# Formula Verification

Machine-readable result: `outputs/checks/formula_verification.json`.

| Formula | Role | Gate | Evidence |
| --- | --- | --- | --- |
| MOB001 | subset-zeta accumulation | verified | 256-table reconstruction |
| MOB002 | Möbius inverse | verified | exhaustive inclusion-exclusion check |
| MOB003 | 3-SAT projector expansion | verified | eight literal polarities |
| MOB004 | routed no-fault roll-up | verified | one-gate limit, 320 routes, fixed-route sensitivity |

The equation is verified independently of route provenance. Exact Eq. (23)
paper values remain blocked because author gate, movement, idle, and busy-time
exposures are unpublished; the current executable exposures are `proxy_model`.
