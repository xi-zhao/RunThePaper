# Paper Map

## Identity

- Paper ID: `2607.27060`
- Title: *Optimising Trotter-Suzuki Simulations of Markovian Open Quantum Systems via Classical Search*
- Authors: S. M. Pillay, I. J. David, I. Sinayskiy, F. Petruccione
- Preprint: arXiv:2607.27060v1 (`publication.status: unverified`)
- Frozen PDF: `../raw/paper.pdf`
- Frozen arXiv source: `../paper-source.tar.gz`
- Author-code boundary: the separately published code archive is intentionally
  not opened, extracted, declared as an input, or used to design the numerical
  implementation. Paper parameters and reported outcomes are sufficient here.

## Reproduction Goal

Independently regenerate every theory-numerical series in Figures 2 and 3 at
the paper parameters.  Each of the eight selected panels contains four visible
series:

1. analytic Trotter-step bound, `N_analytic`;
2. minimum integer Trotter-step count from the verified monotone search,
   `N_min`;
3. gate complexity computed from `N_analytic`, `g_analytic`;
4. gate complexity computed from `N_min`, `g_min`.

The frozen execution scope therefore contains 8 panel targets and 32 visible
theory sequences.  Figure 1 is a lattice schematic and Table 1 is a symbolic
formula catalogue; both are fully inventoried but excluded from generated
reproduction.  Source PNG pixels are reference-only.  No curve tracing,
digitisation, or sampled source pixel enters generated data.

## Paper Structure

| Section | Role | Reproduction relevance |
| --- | --- | --- |
| Abstract | States the analytic-versus-optimised resource claim | Claim context |
| 1 Introduction | Motivates TS product formulas and classical search | Claim context |
| 2 Overview of Simulation Methods | Defines GKSL evolution, four TS-PF channels, four error functions, and gate counts | Direct formula dependencies |
| 3 Derivation of Analytic Bounds | Derives sufficient closed-form bounds on `N` by controlling the exponential | Direct formula dependencies |
| 4 Formulation of the Search Problem | Defines bracketing and binary search for the least acceptable integer `N` | Direct method dependency |
| 5 Results and Discussion | Defines XX-chain and TFIM models, parameter sets, local norm method, and Figures 1–3 | Direct target and parameter source |
| 6 Conclusion | Summarises the resource-reduction and method-ordering claims | Claim context |
| Appendix A | Gives the paper pseudocode for the integer search | Direct method source; independently checked for lower-bound semantics |

## Equation and Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ-GKSL | Sec. 2, Eq. after first paragraph | Markovian master equation | mapped, context |
| EQ-LSUM | Sec. 2, `definition_L` | Decomposes the generator into `M` local terms | mapped, context |
| EQ-TS-DET1 | Sec. 2 | First-order deterministic product formula | mapped, context |
| EQ-TS-RAN1 | Sec. 2 | First-order randomised convex mixture | mapped, context |
| EQ-TS-DET2 | Sec. 2 | Second-order deterministic product formula | mapped, context |
| EQ-TS-RAN2 | Sec. 2 | Second-order randomised convex mixture | mapped, context |
| EQ-ERR-DET1 | Table 1, row 1 | Precision function for Fig. 2a/3a | independently derived and verified |
| EQ-ERR-RAN1 | Table 1, row 2 | Precision function for Fig. 2b/3b | independently derived and verified |
| EQ-ERR-DET2 | Table 1, row 3 | Precision function for Fig. 2c/3c | independently derived and verified |
| EQ-ERR-RAN2 | Table 1, row 4 | Precision function for Fig. 2d/3d | independently derived and verified |
| EQ-N-DET1 | Sec. 3, Proposition 1 in the source | Analytic `N` for first-order deterministic TS-PF | independently derived and verified |
| EQ-N-RAN1 | Sec. 3, Proposition 2 in the source | Analytic `N` for first-order randomised TS-PF | independently derived and verified |
| EQ-N-DET2 | Sec. 3, Proposition 3 in the source | Analytic `N` for second-order deterministic TS-PF | independently derived and verified |
| EQ-N-RAN2 | Sec. 3, Proposition 4 in the source | Analytic `N` for second-order randomised TS-PF | independently derived and verified |
| EQ-GATE-FO | Table 1, rows 1–2 | First-order gate-count proxy `g=MN` | independently verified |
| EQ-GATE-SO | Table 1, rows 3–4 | Second-order gate-count proxy `g=2MN` | independently verified |
| EQ-XX-M | Sec. 5.1 | XX-chain term count `M=2P+3` | independently counted |
| EQ-TFIM-M | Sec. 5.2 | TFIM term count `M=|E_n|+2n` | independently counted |
| EQ-DN-BOUND | Sec. 5.3 | Nechita Choi-matrix upper bound used to obtain `lambda` | mapped; parameter-validation context |
| MTH-BINARY-LOWER-BOUND | Sec. 4 and Appendix A | Finds the least integer `N` satisfying the monotone error inequality | independently verified |
| MTH-PARAMETER-MAP | Sec. 5.4 and captions | Binds paper model, `M` grid, `t`, `lambda`, and `epsilon` to targets | independently verified |

Detailed formula checks are in `DERIVATION_TRACE.md` and
`EQUATION_CARDS.json`; method checks are in `METHOD_TRACE.md`.

## Figure, Panel, Visible-Series, Algorithm, and Table Inventory

| Item | Content | Class | Frozen decision |
| --- | --- | --- | --- |
| Table 1 | Four TS-PF precision functions and gate-count formulas | symbolic table | excluded |
| Fig. 1a–e | TFIM interaction graphs for `n=2,3,4,5,6` | schematic context | excluded |
| Fig. 2a | XX, first-order deterministic; four series `N_analytic`, `N_min`, `g_analytic`, `g_min`; `M=7,9,11,13,15,17,19` | theory numerical | target `T-FIG002A` |
| Fig. 2b | XX, first-order randomised; same four series and grid | theory numerical | target `T-FIG002B` |
| Fig. 2c | XX, second-order deterministic; same four series and grid | theory numerical | target `T-FIG002C` |
| Fig. 2d | XX, second-order randomised; same four series and grid | theory numerical | target `T-FIG002D` |
| Fig. 3a | TFIM, first-order deterministic; four series; `M=5,8,12,15,19` | theory numerical | target `T-FIG003A` |
| Fig. 3b | TFIM, first-order randomised; same four series and grid | theory numerical | target `T-FIG003B` |
| Fig. 3c | TFIM, second-order deterministic; same four series and grid | theory numerical | target `T-FIG003C` |
| Fig. 3d | TFIM, second-order randomised; same four series and grid | theory numerical | target `T-FIG003D` |
| Algorithm 1 | Doubling bracket plus binary search | algorithm trace | method dependency |

Every Fig. 2/3 sequence is a formula-generated theoretical sequence.  There
are no experimental points, images, or source-derived fit inputs in either
selected figure.

## Paper Parameters

| Model | Parameters | Source |
| --- | --- | --- |
| XX chain | `P=2..8`, `M=2P+3=[7,9,11,13,15,17,19]`, `Omega=3.94`, `gamma=0.31`, `lambda=7.071`, `epsilon=1e-3`, `t=2` | Secs. 5.1 and 5.4; Fig. 2 caption and plotted M grid |
| TFIM | `n=2..6`, `M=[5,8,12,15,19]`, `J=1`, `h=0.5`, `gamma=0.1`, `lambda=8.00`, `epsilon=1e-5`, `t=5` | Secs. 5.2 and 5.4; Fig. 3 caption |

The published figures use the reported `lambda` values as numerical inputs.
The reproduction preserves those paper-exact values and separately checks the
parameter/method chain; it does not infer values by sampling the plotted PNG.

## Claims

| Claim ID | Paper claim | Target support |
| --- | --- | --- |
| CLM-ANALYTIC-SUFFICIENCY | The four closed-form `N_analytic` expressions are sufficient for the stated error bounds | all eight targets |
| CLM-SEARCH-MINIMUM | Monotone integer search finds the least `N` satisfying `epsilon_hat <= epsilon` | all eight targets |
| CLM-EMPIRICAL-REDUCTION | `N_min` and `g_min` are substantially smaller than their analytic counterparts | all eight targets |
| CLM-METHOD-ORDERING | Randomised formulas improve scaling with `M`; second-order randomised has the lowest resource counts over the plotted grids | Fig. 2b/d and Fig. 3b/d, checked against all methods |
| CLM-RAN1-DET2-N | First-order randomised and second-order deterministic use identical `N` but second-order deterministic uses twice the gates | Fig. 2b/c and Fig. 3b/c |

## Assumptions and Boundaries

- `N_min` is an optimised bound obtained by solving the paper's stated error
  inequality; it is not a direct diamond-norm simulation of the full channel.
- Gate complexity is the paper's proxy (`M N` or `2 M N`), not a hardware-native
  gate compilation count.
- Random sampling or quantum forking is not executed because the selected
  figures evaluate deterministic precision bounds, not stochastic simulation
  outcomes.
- The source PNGs provide only layout and visual-reference evidence.
- The separately published author code is outside the evidence boundary; the
  implementation is derived from the paper equations, captions, and axes.
- Local CPU and available disk are sufficient: the target calculation is
  `O(number of M values × log N)` with negligible memory use; no remote service
  or accelerator is required.
