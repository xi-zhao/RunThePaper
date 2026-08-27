# Paper Map

## Identity

- Paper ID: `10.1103-PRXQuantum.6.010331`
- Published title: *Benchmarking and Fidelity Response Theory of High-Fidelity Rydberg Entangling Gates*
- Authors: Richard Bing-Shiun Tsai, Xiangkai Sun, Adam L. Shaw, Ran Finkelstein, Manuel Endres
- Preprint: arXiv:2407.20184v2 (19 November 2024)
- Formal publication: *PRX Quantum* **6**, 010331 (2025)
- DOI: `10.1103/PRXQuantum.6.010331`
- Local PDF: `raw/paper.pdf`
- Local text: `raw/paper.txt`
- Local TeX source: `paper-source/main.tex`
- Original source figures: `paper-source/MTFigs/` and `paper-source/SIFigs/`

## Reproduction Goal

The executable scope is now **all theoretical content that can be calculated
from published formulas, printed parameters, or public primary-source control
protocols**. Every plotted CSV is generated before any source figure is read.
Paper pixels are permitted only in the post-computation side-by-side renderer;
`outputs/checks/computational_provenance_audit.json` enforces this boundary.

The nine durable targets cover Figs. 6(a), 7, 8, 9(a,b), 10 (analytic filter),
11 (explicit seven-site reconstruction), 12 (cavity transfer), 15, and 17,
including the theoretical component of Fig. 1(f). A target is called
paper-exact only when its numerical inputs are fully published. Otherwise the
missing parameters remain explicit and the artifact is labelled `paper_subset`
or `proxy_model`; no source curve is digitized to fill the gap.

Experimental traces, measured PSD arrays, and the complete calibrated
Monte-Carlo error model remain blocked because their numerical inputs are not
released with the article or source bundle. The corresponding formulas and
mechanisms are reproduced wherever they close independently.

## Paper Structure

| Section | Role | Reproduction relevance |
| --- | --- | --- |
| I. Introduction | Product claim and result summary | Defines fidelity `0.9971(5)` and the two contributions: SSB + FRT. |
| II. Benchmarking | SSB circuit and full error model | Experimental/model context; raw data and calibrated model are not released. |
| III. Fidelity response theory | Core theoretical model | Primary executable scope. |
| IV. Applications | Rydberg-state, gate-protocol, spin-lock and many-body uses | Formula-complete subsets reproduced as T004-T006 and T009. |
| V. Towards 0.999 | Hardware-upgrade projection | Cavity transfer reproduced as T007; absolute projection needs measured PSD/full model. |
| Appendices A-F | Experimental/model details and SSB analysis | Context and exact tables; insufficient for an independent full-model rerun. |
| Appendix G | Derivation of the FRT response | Formula gate source. |
| Appendices H-K | Spin-lock, experimental response, realistic/two-photon extensions | Supporting/future targets. |
| Appendix L | Six-parameter universal-response fits | Paper-exact executable target for Fig. 15. |

## Equation Inventory

| Card | Paper source | Role | Gate status |
| --- | --- | --- | --- |
| EQ001 | Eq. (12) | Ideal infinite-blockade two-atom Hamiltonian | verified |
| EQ002 | Ref. 8 / cited Evered Methods | Generic sinusoidal pulse for the direct diagnostic | reconstructed; Fig. 15 identity unverified |
| EQ003 | Eq. (9), Appendix Eq. (G7) | Haar-averaged connected response | verified |
| EQ004 | Eqs. (13)-(14) | Frequency and relative-intensity noise operators | verified |
| EQ005 | Eqs. (15)-(16) | Universal Rabi-frequency scaling | verified |
| EQ006 | Appendix L | Four analytic response functions used by the final targets | source + limiting-case checks |
| EQ007 | Eqs. (10)-(11), Fig. 7, Appendix D | PSD-weighted error budget and power laws | verified |
| EQ008 | Fig. 8 text | Fixed-power principal-quantum-number scaling | reconstructed from printed anchors |
| EQ009 | Cited primary protocol papers | Three CZ control sequences | verified; Fromonteil variant identity disclosed as reconstructed |
| EQ010 | Appendix H | Finite-time spin-lock response | verified |
| EQ011 | Fig. 11 text | Seven-site Rydberg Hamiltonian | reconstructed where geometry/ramp metadata are absent |
| EQ012 | Appendix D | Phase-flip fidelities and first-order SSB proxy | verified |
| EQ013 | Fig. 12 text | 140 kHz cavity power transfer | reconstructed convention |

## Figure Inventory

| Item | Scientific content | Initial class | Current scope |
| --- | --- | --- | --- |
| Fig. 1 | Experimental overview, error budget and FRT scaling | mixed | panel (f) mechanisms reproduced by T003; exact full budget needs PSD/full model |
| Fig. 2 | SSB circuit and phase calibration | schematic/experimental | context |
| Fig. 3 | Experiment vs six full-model fidelity metrics | numeric + experimental | blocked by calibrated full model/raw traces |
| Fig. 4 | Full-model response under separate noise sources | numeric | blocked by calibrated model/noise traces |
| Fig. 5 | SSB sensitivity to clock-gate errors | numeric | abstract sensitivity mechanism reproduced by T008; calibrated curve blocked |
| Fig. 6 | FRT response, measured PSDs and contribution histograms | mixed | panel (a) reproduced from Appendix L; panels (b,c) need raw PSD |
| Fig. 7 | Error-source power laws vs Rabi frequency | numeric | four power laws and public absolute terms reproduced; PSD/Doppler amplitudes blocked |
| Fig. 8 | Fidelity vs Rydberg principal quantum number | numeric | public-anchor Rabi/spacing scaling reproduced; total infidelity optimum blocked |
| Fig. 9 | Gate-protocol comparison | numeric | panels (a,b) independently propagated; panel (c) needs experimental amplitudes |
| Fig. 10 | Spin-lock noise spectroscopy | numeric + experimental | exact finite-time filter reproduced; absolute PSD/data comparison blocked |
| Fig. 11 | Seven-qubit many-body response | numeric | 128-dimensional physical reconstruction generated; paper-exact geometry/ramp unavailable |
| Fig. 12 | Cavity filtering and route to 0.999 | numeric + experimental model | 140 kHz transfer reproduced; filtered PSD/full model blocked |
| Fig. 13 | Raw SSB decay traces | experimental | not reproduced |
| Fig. 14 | Pair-resolved SSB fidelity | experimental | not reproduced |
| Fig. 15 | Universal Haar and symmetric-Haar responses | numeric | primary analytic reproduction target |
| Fig. 16 | Benchmark-sequence comparison | schematic + numeric | mechanism covered by T008; exact calibrated panel (b) blocked |
| Fig. 17 | Abstract phase-flip/depolarizing model | numeric | printed analytic curves reproduced; full quadratic circuit inset blocked by missing discrete realization |
| Fig. 18 | Injected-noise experimental response | experimental | validation value only |
| Tables I-III | Symmetric stabilizer states and circuit rotations | method/configuration | context for future SSB target |
| Table IV | Experimental and full-model fidelities | numeric table | exact source values available; independent rerun blocked |
| Table V | Shot-to-shot coherent/incoherent noise simulations | numeric table | full-model inputs unavailable |
| Table VI | Leakage correction | experimental + model table | raw measurements unavailable |

## Parameter Sources And Assumptions

- Fig. 15 uses all four Appendix-L functional forms and coefficient sets;
  provenance is `analytic_reference`, not an independent recovery of the
  unpublished optimized trajectory.
- Fig. 9 propagates the infinite-blockade Hamiltonian using public Evered,
  Levine-Pichler, and Fromonteil controls. The selected Fromonteil Protocol-II
  variant is disclosed because the target paper does not identify the discrete
  sequence variant.
- Fig. 11 uses the printed `N=7`, `Omega/(2*pi)=7.7 MHz`, `T=6 us`, and
  detuning endpoints. `V_nn/Omega=20` and tangent shape `1.35` are explicit
  reconstruction parameters, never image-fitted parameters.
- Fig. 12 uses a disclosed single-pole **power** transfer with `f_c=0.14 MHz`;
  the paper states the linewidth but not the convention.
- Fig. 17 evaluates the printed Appendix-D formulas with `N=10`; that value is
  printed for the phase-calibration SSB sequence but is not explicitly attached
  to Fig. 17, so the full circuit inset remains partial.
- All unavailable PSDs, Doppler variances, electric-field arrays, calibration
  distributions, and exact pulse/ramp metadata stay missing. They are never
  inferred from raster images.
