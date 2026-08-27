# Figure Classification

Only numerical content can become executable reproduction evidence. Mixed
figures are classified panel-by-panel so source images and experimental traces
cannot be mistaken for generated physics.

| Paper item | Class | Reproduce in this pass? | Reason |
| --- | --- | --- | --- |
| Fig. 1(a,b) | `experimental_context` | No | Atom image and measured SSB decay. |
| Fig. 1(c) | `numeric_reproduction` | Exact blocked | Full error budget needs measured PSDs and calibrated hardware model. |
| Fig. 1(f) | `numeric_reproduction` | Partial: T003 | Four scaling laws plus public intensity/lifetime terms are calculated; absolute PSD/Doppler terms are unavailable. |
| Fig. 1(d,e) | `schematic_context` | No | Level/pipeline illustrations. |
| Fig. 2(a) | `schematic_context` | No | Circuit diagram. |
| Fig. 2(b) | `experimental_context` | No | Measured phase calibration. |
| Fig. 3 | `numeric_reproduction` | No, blocked | Full ab-initio trajectories and clock/Rydberg error parameters are incomplete. |
| Fig. 4 | `numeric_reproduction` | No, blocked | Requires the same full stochastic model and measured noise traces. |
| Fig. 5 | `numeric_reproduction` | Mechanism only: T008 | Appendix-D phase-flip mechanism is calculated; calibrated full-model points are unavailable. |
| Fig. 6(a) | `numeric_reproduction` | Yes | Appendix-L universal response and Eqs. (15)-(16) rescaling. |
| Fig. 6(b) | `experimental_context` | No | Measured laser PSD arrays are not released. |
| Fig. 6(c) | `numeric_reproduction` | No, blocked | Numerical histogram depends on the unreleased PSD arrays. |
| Fig. 7 | `numeric_reproduction` | Partial: T003 | Formula power laws and published absolute terms generated; exact PSD/Doppler amplitudes blocked. |
| Fig. 8 | `numeric_reproduction` | Partial: T004 | Printed-anchor Rabi/spacing scaling generated; full atomic/noise error minimum blocked. |
| Fig. 9(a,b) | `numeric_reproduction` | Yes: T005 | Three public controls independently propagated through the two-atom Hamiltonian. |
| Fig. 9(c) | `numeric_reproduction` | Exact blocked | Requires experimental PSD and atomic-motion amplitude. |
| Fig. 10 | `numeric_reproduction` + `experimental_context` | Partial: T006 | Finite-time spin-lock filter calculated; absolute decay/data curves need author PSD and measurements. |
| Fig. 11 | `numeric_reproduction` | Physical reconstruction: T009 | Seven-site 128D dynamics calculated; exact geometry and ramp metadata are missing. |
| Fig. 12 | `numeric_reproduction` | Partial: T007 | 140 kHz cavity transfer generated; filtered PSD and full-model projection blocked. |
| Fig. 13 | `experimental_context` | No | Raw SSB measurements. |
| Fig. 14 | `experimental_context` | No | Pair-resolved measurements. |
| Fig. 15 | `numeric_reproduction` | Yes | Complete Appendix-L analytic universal response target. |
| Fig. 16(a,c) | `schematic_context` | No | Circuit diagrams. |
| Fig. 16(b) | `numeric_reproduction` | Mechanism only: T008 | First-order SSB sensitivity is calculated; exact calibrated circuit curve is blocked. |
| Fig. 17 | `numeric_reproduction` | Partial: T008 | Printed analytic formulas generated; full quadratic circuit inset lacks an exact circuit realization. |
| Fig. 18 | `experimental_context` | No | Injected-noise measurement; numerical value retained as a sanity reference. |
| Table I | `algorithm_trace` | No | Defines the 12 symmetric stabilizer states. |
| Tables II-III | `algorithm_trace` | No | Defines SSB initialization/recovery rotations. |
| Table IV | `numeric_reproduction` | No, blocked | Exact printed values are available; independent model rerun is not. |
| Table V | `numeric_reproduction` | No, blocked | Requires unpublished shot-noise distributions and full model. |
| Table VI | `experimental_context` | No | Measured/simulated leakage correction values. |

## Active Numerical Scope

- `T001`: Fig. 15, both panels, Appendix-L analytic universal response.
- `T002`: Fig. 6, panel (a) rescaled from `T001`; panel (b) is experimental
  context and panel (c) remains explicitly unavailable.
- `T003`: Fig. 1(f)/Fig. 7 formula power laws and public absolute terms.
- `T004`: Fig. 8 fixed-power Rabi and blockade-spacing scaling.
- `T005`: Fig. 9(a,b), independent eight-dimensional Hamiltonian responses for
  three public CZ control protocols.
- `T006`: Fig. 10 finite-time spin-lock filter.
- `T007`: Fig. 12 140 kHz cavity transfer.
- `T008`: Fig. 17 Appendix-D phase-flip and first-order SSB formulas; also the
  theoretical mechanism relevant to Figs. 5 and 16(b).
- `T009`: Fig. 11 seven-site, 128-dimensional quench/adiabatic reconstruction.

The reconstructed direct Hamiltonian response is diagnostic `D001`, not a
scored paper target, because the exact Fig. 15 phase trajectory is unavailable.

The status words are deliberately non-interchangeable:

- `Yes` means the published formula/parameter subset is numerically closed.
- `Partial` means the available theoretical mechanism is calculated, while an
  exact paper curve still requires unpublished numerical inputs.
- `Physical reconstruction` means a real Hamiltonian is solved with every
  additional assumption printed in the config; it is not paper-exact.
- `Exact blocked` means generating the original curve would require author
  arrays or metadata. Raster pixels are not accepted as replacements.
