# Consistency Report

## Matches

| Feature | Paper | Local result | Level |
| --- | --- | --- | --- |
| Noninteracting peak drift | Peak tracks pulse imperfection | Analytic free-spin peak moves away from `1/2` as `epsilon` grows | feature_match |
| Interacting peak rigidity | Peak remains locked at `omega/2` | `L=14` interacting simulation locks at `1/2`; max locking error `0.0` | feature_match |
| Variance peak | `Var(h)` peaks near the transition | `Var(h)` peak appears in nearest-neighbor scans | feature_match |
| Long-range variance | `alpha=1.5` model has variance peak | Local long-range `L=10` model has a clear variance peak | feature_match |
| Mutual information flow | DTC side has long-range mutual information, trivial side drops | Corrected endpoint MI gives `log 2` at `epsilon=0` and drops near zero at large detuning | feature_match |

## Partial

| Feature | Reason |
| --- | --- |
| Level statistics crossing | The same observable is generated through `L=10`, but the original crossing needs far more disorder realizations. |
| Phase diagram | Local boundary proxy uses only the `Var(h)` peak. The paper combines multiple diagnostics. |
| Mutual information scaling collapse | The finite-size flow is reproduced, but the scaling collapse and critical exponents are not rerun at the original scale. |
| Critical exponents | Not accepted. Requires the full finite-size scaling campaign. |

## Not In Scope

- Experimental schematic inset in Fig. 4.
- Full trapped-ion experimental implementation details.

Supplementary clean-vs-disordered spectra are now in scope and code-ready as ten separately enumerated numerical panels.

## Paper-audit state

- No current paper-error candidate is asserted.
- The paper itself acknowledges that an earlier manuscript version omitted coupling-strength disorder from Eq. (1), although the numerical simulations included it. The reviewed version is corrected; this is not a newly discovered error.
- Supplement Fig. S1(c) has an implementation-level ambiguity, so a quantitative mismatch must first be tested against alternative text-compatible susceptibility definitions.
- Full paper-scale execution and fresh-context review are still missing; disagreement from smoke or reduced-scale data cannot be attributed to the paper.

## Final Label

`feature_reproduced_full_scope_code_ready_production_blocked`
