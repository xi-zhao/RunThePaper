# Target Ledger — PRB 91, 085420 (2015)

All targets use the paper's published physical parameters
(`parameter_match = paper_exact`), independent numerics
(`generated_data_provenance = independent_numerics`), and a `verified` formula
gate. Unpublished discretization choices are frozen independent numerical
settings, not claimed as paper parameters. The paper is raster-only (no author data), so the
reference comparison is a source-vs-reproduction feature contract
(`reference_comparison = visual_feature_contract`), which caps each target at 80.

| ID | Figure | Quantity | Paper params | Stage | Score |
| --- | --- | --- | --- | --- | --- |
| T101 | Fig. 1(a,b) | Floquet spectrum omega(k,beta); initial populations rho_{n,k}(0) | J=K=3, alpha=1/3, tau=2 | final | 80 |
| T201 | Fig. 2(a,b) | one-cycle Delta rho_{n,k}: actual vs Eq. (8) | J=K=3, T=1024 | final | 78 |
| T301 | Fig. 3 | <x>(t) over one cycle, 6 durations; Eq. (13) vs Berry-only | J=K=4, T=1024..6144 | final | 80 |
| T401 | Fig. 4 | Delta<x> vs J transition probe; actual/theory/Berry-only | J=K in [5.0,5.3], T=2560 | final | 80 |

Overall: **79.5 / 100 — numerical feature reproduction** (all four figures).

## Parameter cards (paper vs generated)

**T101** — paper: J=K=3, alpha=1/3, tau=2, k in [-pi/3,pi/3], beta in [0,2pi],
site-0 initial state. Generated: identical; 61x61 (k,beta) grid for the surface,
241 k-points for populations, n_sub=120. `paper_exact`.

**T201** — paper: J=K=3, T=1024, one pumping cycle, bottom band emphasised.
Generated: identical; Nk=401, n_sub=160; all three bands shown (2x3 grid).
Actual = exact per-k dynamics; theory = Eq. (8) with exact discrete accumulated
phase. `paper_exact`.

**T301** — paper: J=K=4, T in {1024,2048,3072,4096,5120,6144}, piecewise-constant
beta (one step per driving period). Generated: identical six durations; Nk=2T
(4096..12288, convergence-verified), n_sub=100; theory Eq. (13) at Nk=401.
`paper_exact`.

**T401** — paper: J=K in [5.0,5.3] (T=2560), transition at ~5.14. Generated:
61-point scan, T=2560, Nk=5120, n_sub=100; theory Eq. (13) per J. `paper_exact`
for the physical parameters, with the grid declared as an independent numerical
choice.

## Compute

Every target ran locally on an Apple M4 (16 GiB), no remote resources. The
adiabatic cycle is the ordered product of T one-period 3x3 Floquet operators
(beta piecewise-constant), and a Strang split precomputes the fixed hopping
propagator — so even T=6144 and the 61-point J-scan finish in minutes. The
isolated no-render campaign took 998.84 s. No reduced-scale or proxy
substitution was used.
