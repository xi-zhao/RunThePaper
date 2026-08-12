# Method trace

| Paper method | Independent implementation | Verification |
|---|---|---|
| Periodic hexagonal `N`-cell tiling | `topology.build_hexagonal_tiling` | exact `V=2N`, `E=3N`, trivalence, two cells/edge, torus `V-E+F=0` |
| Bidisperse target areas/perimeters | `VertexTissue.initialize` | target-area sum equals box area; 1:1 population and area ratio `1:1.4^2` |
| Eq. (1) energy and Appendix force | `geometry.polygon_observables`, `model.elastic_forces` | central finite differences, zero net cell force, passive energy descent |
| Eq. (2) shear dynamics | reduced sheared lattice `H(t)` in `model.step` | lattice-remap pair displacements and Lees–Edwards equivalence |
| Eqs. (3–4) rotational diffusion | Euler–Maruyama angle update | variance identity `2 Dr dt` |
| Eq. (5) active weighting | `model.active_forces` | exact printed normalization; uniform polarization gives force `v/6` |
| T1 neighbor exchange | `topology.perform_t1` | four-cell incidence, new perpendicular edge, topology invariants |
| Eq. (6) stress | `model.cell_stress_tensors` | translation invariance and signed/magnitude separation |
| Preparation and shear protocol | `campaign.prepare_model`, `execute_condition` | immutable config, shared prepared state, disjoint conditions/seeds |
| Steady-state statistics | chunked scalar time series and three-seed aggregation | gap/overlap rejection and hash-bound checkpoint resume |
| Figs. 2–7 analysis | `analysis.py`, `rendering.py` | threshold definitions, fit residuals, alternative collapse exponent |

The implementation was written without requesting or inspecting the author code. Renderers consume only generated result files. The numerical runner has no path to `raw/` or `references/` in its isolated contract.
