# Figure Classification

Only numerical figures/tables become executable reproduction targets.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Fig. 1 | `schematic_context` | No | ORMD waveform examples for the *purely two-body* gate; illustrative, not the BAM result. |
| Fig. 2 | `schematic_context` | No | Atomic level diagrams and geometric cartoons of the buffer-atom layout. |
| **Fig. 3 (a–c)** | `numeric_reproduction` | **Yes** | Single-photon BAM CZ, hybrid modulation: waveforms + populations + phases, B=2π·50 MHz. **Primary target.** |
| **Fig. 3 (d–f)** | `numeric_reproduction` | **Yes** | Single-photon BAM CZ, amplitude-only modulation. **Primary target.** |
| **Fig. 4** | `numeric_reproduction` | **Yes (hybrid) / partial (amplitude)** | Two-photon ground-Rydberg CZ via the full three-level (a5/a6) model. Hybrid (a-c) populations digitized to <0.4% RMS; amplitude-only (d-f) partial. Full-model gate error ~1e-3 vs paper <1e-4. T004/T005. |
| **Fig. 5** | `numeric_reproduction` | **Yes** | Dual-pulse Doppler-insensitive CZ. All three panels reproduced; dual-pulse conditional phase 0.99988π; first-order Doppler cancellation demonstrated (~2600-32000× suppression). T006. |
| Fig. 6 | `numeric_reproduction` | **Attempted — not reproduced** | Three-qubit Toffoli phase-gate part, two-photon. The two-photon model runs but the multi-qubit buffer geometry is not specified in the paper; the best-guess star geometry gives 11% leakage in the 4-atom (256-state) sector — not a match. Coefficients recorded (coefficients.py comment). |
| **Fig. 7** | `numeric_reproduction` | **Yes (feature)** | Gate-error colormap vs. overall Rabi-amplitude ratio; reuses the Fig. 3(a) machinery with a 2-D ratio scan. Structure reproduced; peak ~25% low. T003. |
| Figs. a1–a3 | `schematic_context` | No | Level/linkage diagrams underlying the appendix Hamiltonians (a1)–(a6). |
| Fig. a4 | `schematic_context` | No | Cartoon of buffer-atom-relay lattice geometries. |
| Fig. a5 | `numeric_reproduction` | Deferred | Time evolution of a single dual-pulse; same physics as the reproduced Fig. 5. |
| Figs. a6–a8 | `numeric_reproduction` | **Not reproducible** | Extra BAM examples at B=2π·100 MHz. The paper gives no waveform coefficients for these (sample figures only), so they cannot be reproduced without re-solving the inverse waveform-design problem. |
| Tables a1–a2 | `algorithm_trace` | No | Buffer-atom-relay CZ bookkeeping (state tables), not a numerical figure. |

## Scope summary

- **In scope / reproduced now:** Fig. 3 (a–f) — the central single-photon BAM CZ
  result. These carry the paper's headline claim (gate error < 10⁻⁴) and are
  fully specified (waveform coefficients + Hamiltonians a1/a3/a4).
- **Exploratory:** Fig. 5 single pulse (coefficients in `coefficients.py`).
- **Deferred (recorded, not run):** the two-photon protocols (Fig. 4/6/a7/a8),
  the Fig. 7 ratio scan, and the B=100 MHz examples (a6). All feasible locally;
  see `PLANNED_LARGE_SCALE_RUNS.md` for the follow-up plan.

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`
