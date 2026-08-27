# Formula Verification

This case uses `EQUATION_CARDS.json` as the machine-readable formula map.

Machine-readable result: `outputs/checks/formula_verification.json`.

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| BBTN001 | Output probability | verified | Source-traced and implemented by direct amplitude lookup. |
| BBTN002 | Bitstring split | verified | Source-traced and implemented by the proxy batch selection. |
| BBTN003 | Head-tail amplitude factorization | verified | The clean-room public-circuit check explicitly constructs `v_head`, contracts independent tail rows, and agrees with direct amplitudes. |
| BBTN004 | XEB fidelity | verified | Source-traced and implemented by the XEB/post-selection code. |
| BBTN005 | Porter-Thomas distribution | verified | Source-traced and implemented as the analytic reference. |
| BBTN006 | Conditional probability | verified | Source-traced and normalization-checked in the proxy data. |
| BBTN007 | Shared-head batch reuse cost | verified | One reduced public-circuit head is reused for four checked amplitudes, and the printed cost arithmetic is evaluated explicitly. |
| BBTN008 | Complete-subspace marginal/XEB identity | verified | Eq. (1), the complete suffix batch, and the marginal definition give `F_XEB+1=2^n_closed P(s_closed)` exactly. |
| BBTN009 | Complex64/complex128 diagnostics | verified | Three reduced public-circuit sizes record amplitude, probability, norm, and fidelity differences; the paper-scale acceptance contract remains source-audited as missing. |
| BBTN010 | Complex64 tensor memory | verified | Runtime dtype inspection and exact decimal/binary unit conversions verify `M=2^rank*8` bytes. |

Formula verification establishes what the implementation computes; it does not assign a paper verdict. T005's exact 345/36 membership and T009's paper-scale precision acceptance contract remain publication-underspecified. T012/T013 source inconsistencies remain for fresh independent review.
