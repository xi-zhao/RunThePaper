# Target Ledger

## Active Targets

| Target ID | Paper item | Type | Formula dependencies | Formula gate | Status | Data output | Figure output | Check output | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Fig. 15 | Appendix-L analytic response | EQ005-EQ006 | source_only | `reproduced_envelope` | `outputs/data/universal_response.csv` | `outputs/figures/fig15_universal_response.png` | `outputs/checks/universal_response.json` | All published fit coefficients used; approximate intensity fit omits small side peaks near `x=1.5,2.5`. |
| T002 | Fig. 6 | dimensional rescaling | EQ005-EQ006 | source_only | `physically_consistent_envelope` | `outputs/data/fig6a_scaled_response.csv` | `outputs/figures/fig6a_scaled_response.png` | `outputs/checks/fig6a_scaled_response.json` | Panel (a) envelope; collapse error `1.42e-14`; fine peaks, PSD, and panel (c) remain open. |
| T003 | Fig. 1(f), Fig. 7 | FRT error-budget scaling | EQ006-EQ007 | verified | `paper_subset` | `outputs/data/fig7_formula_scalings.csv` | `outputs/figures/fig7_formula_scalings.png` | `outputs/checks/formula_theory_targets.json` | Four exact power laws; 0.8% intensity and 78/166 us lifetime terms absolute. PSD/Doppler amplitudes stay open. |
| T004 | Fig. 8 | principal-quantum-number scaling | EQ008 | reconstructed | `paper_subset` | `outputs/data/fig8_public_anchor_scaling.csv` | `outputs/figures/fig8_public_anchor_scaling.png` | `outputs/checks/formula_theory_targets.json` | Passes printed `n=61, 7.7 MHz, 3.3 um` and `n=44, 13 MHz, 1.7 um` anchors. Total optimum needs missing arrays. |
| T005 | Fig. 9(a,b) | direct gate-protocol responses | EQ001, EQ003-EQ004, EQ009 | verified | `independent_hamiltonian_numerics` | `outputs/data/fig9_protocol_responses.csv` | `outputs/figures/fig9_protocol_responses.png` | `outputs/checks/formula_theory_targets.json` | Three gates propagated in 8D; closure and CZ phase checked. Panel (c) needs experimental noise amplitudes. |
| T006 | Fig. 10 | finite-time spin-lock filter | EQ010 | verified | `paper_subset` | `outputs/data/fig10_spin_lock_filter.csv` | `outputs/figures/fig10_spin_lock_filter.png` | `outputs/checks/formula_theory_targets.json` | Sinc-squared resonance and lifetime-floor formula implemented; absolute PSD/data curve blocked. |
| T007 | Fig. 12 | cavity transfer | EQ013 | reconstructed | `proxy_model` | `outputs/data/fig12_cavity_transfer.csv` | `outputs/figures/fig12_cavity_transfer.png` | `outputs/checks/formula_theory_targets.json` | 140 kHz single-pole power transfer; convention disclosed. Absolute filtered PSD/full model blocked. |
| T008 | Fig. 17; mechanism for Figs. 5/16 | SSB phase-flip proxy | EQ012 | verified | `paper_subset` | `outputs/data/fig17_phase_flip_first_order.csv` | `outputs/figures/fig17_phase_flip_first_order.png` | `outputs/checks/formula_theory_targets.json` | Printed product/symmetric fidelities and first-order cancellation generated. Full circuit inset lacks exact discrete realization. |
| T009 | Fig. 11 | seven-site many-body response | EQ003, EQ011 | reconstructed | `proxy_model` | `outputs/data/fig11_many_body_responses.csv` | `outputs/figures/fig11_many_body_responses.png` | `outputs/checks/formula_theory_targets.json` | Independent 128D dynamics; max norm error `6.35e-14`, final Z2 probability `0.999985`. Exact geometry/ramp metadata unavailable. |

## Diagnostic Target

| Target ID | Purpose | Parameter match | Status | Evidence | Why it is unscored |
| --- | --- | --- | --- | --- | --- |
| D001 | Direct FRT integration of the ideal eight-dimensional Rydberg model | `reconstructed` | `partial` | `outputs/checks/direct_response_diagnostic.json` | The cited generic pulse gives a high-fidelity CZ, but the paper does not release the exact Fig. 15 trajectory and the response shape differs from Appendix L. |

## Exact Paper Curves Still Blocked

| Paper item | Status | Blocking input or next action |
| --- | --- | --- |
| Fig. 1(c), Figs. 3-4 | `blocked_missing_parameter` | Measured PSD arrays, realistic pulse trace and complete ab-initio calibration. |
| Fig. 5, Fig. 16(b) | `blocked_missing_parameter` | Calibrated clock/Rydberg channel parameters and exact SSB circuit realization; analytic mechanism is covered by T008. |
| Fig. 6(c), absolute Fig. 7, full Fig. 12 | `blocked_missing_parameter` | Raw frequency/RIN PSD arrays and full-model calibration; source raster is comparison-only evidence. |
| Full Fig. 8 | `blocked_missing_parameter` | State-dependent lifetime, temperature, PSD, electric-field-noise and polarizability arrays. |
| Fig. 9(c) | `blocked_missing_parameter` | Experimental PSD and atomic-motion amplitude. |
| Absolute Fig. 10 | `blocked_missing_parameter` | Experimental spin-lock traces and numerical PSD. |
| Paper-exact Fig. 11 | `blocked_missing_parameter` | Atom geometry, C6/r^6, exact Rabi ramp and tangent-shape metadata. |
| Fig. 17 full quadratic inset | `blocked_missing_method` | Exact Fig. 17 circuit length and recovery realization. |
| Tables IV-V | `blocked` | Printed values can be validated, but independent rerun needs full model inputs. |

The machine similarity score remains scoped to the two paper-exact analytic
reference targets `T001-T002`; `T003-T009` are tracked as independent formula
numerics with explicit scope caps rather than being rewarded for visual
resemblance. The provenance audit proves that no source-figure pixels enter any
of these calculations.
