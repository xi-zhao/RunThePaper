# Target Ledger

Each numerical execution/evidence target gets one entry. `Atomic panels` records
the independently adjudicable paper items backed by that target; one shared
numerical run may generate several panels without collapsing the panel-level
coverage denominator.

| Target ID | Paper item | Atomic panels | Type | Formula dependencies | Formula gate | Status | Data output | Figure output | Check output | Notes |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 1 views 1-2 | 2 | geometric numerics | EQ002-EQ004 | verified | reproduced | `outputs/data/t001_spin1_foliation.csv` | `outputs/figures/t001_spin1_foliation.png` | `outputs/checks/t001_spin1_foliation.json` | Paper-exact analytic geometry; both source viewing angles are independent items. |
| T002 | Main Fig. 2 left r1c1-r2c3 | 6 | exact diagonalization | EQ002-EQ006 | verified | reproduced | `outputs/data/campaign_shards/main_L*_typicality.csv` | `outputs/figures/t002_main_typicality.png` | `outputs/checks/t002_figure.json` | Two observables by three temperatures; boundary/shell metadata remain disclosed reconstructions. |
| T003 | Main Fig. 2 right | 1 | exact dynamics | EQ002-EQ007 | verified | reproduced | `outputs/data/t003_dynamics.csv` | `outputs/figures/t003_dynamics.png` | `outputs/checks/t003_dynamics.json` | \(L=12,\beta=0.5,t\in[0,3]\); exact mixed/representative curves, sampled shell bands. |
| T004 | Supp. Fig. S1 r1c1-r4c3 | 12 | exact diagonalization | EQ002-EQ006 | verified | reproduced | `outputs/data/campaign_shards/supplemental_L*_typicality.csv` | `outputs/figures/t004_s1_beta025.png` | `outputs/checks/t004_figure.json` | All 12 observables, four paper sizes, and commuting-leaf benchmarks pass. |
| T005 | Supp. Fig. S2 r1c1-r4c3 | 12 | exact diagonalization | EQ002-EQ006 | verified | reproduced | same campaign shards | `outputs/figures/t005_s2_beta075.png` | `outputs/checks/t005_figure.json` | All 12 observables, four paper sizes, and commuting-leaf benchmarks pass. |
| T006 | Supp. Fig. S3 r1c1-r4c3 | 12 | exact diagonalization | EQ002-EQ006 | verified | reproduced | same campaign shards | `outputs/figures/t006_s3_beta175.png` | `outputs/checks/t006_figure.json` | All 12 observables, four paper sizes, and commuting-leaf benchmarks pass. |
| T007 | Supp. Fig. S4 r1c1-r4c3 | 12 | exact diagonalization | EQ002-EQ006 | verified | reproduced | `outputs/data/campaign_shards/integrable_L*_typicality.csv` | `outputs/figures/t007_s4_integrable.png` | `outputs/checks/t007_figure.json` | Swapped integrable dynamics and its commuting-leaf benchmark pass at all paper sizes. |
| T008A | Supp. Fig. S5 row 1, three temperatures | 3 | spectral decomposition | EQ002-EQ003, EQ006, EQ009 | verified | reproduced | `outputs/data/campaign_shards/main_L12_compression.csv` | `outputs/figures/t008a_main_compression.png` | `outputs/checks/t008a_figure.json` | \(L=12\) main-family participation clouds. |
| T008B | Supp. Fig. S5 row 2, three temperatures | 3 | spectral decomposition | EQ002-EQ003, EQ006, EQ009 | verified | reproduced | `outputs/data/campaign_shards/supplemental_L12_compression.csv` | `outputs/figures/t008b_supp_compression.png` | `outputs/checks/t008b_figure.json` | \(L=12\) supplemental-family participation clouds. |
| T009 | Supp. Fig. S6 left-right | 2 | finite-size scaling | EQ002-EQ003, EQ006, EQ009 | verified | reproduced | campaign compression shards | `outputs/figures/t009_entropy_gain.png` | `outputs/checks/t009_figure.json` | Both \(h_{0,z}\) panels and \(L=8,9,10,11,12\) pass; minimum gain is positive. |

## Paper-Parameter Cards

### Shared spin-chain definition

- Paper source: Eq. (9), Main Fig. 2 caption, Supplemental Eq. (S1), and
  Supplemental figure captions in `paper-source/main.tex`.
- Dynamics Hamiltonian:
  \[
  H=\sum_{\ell=1}^{L}\left[
  \sigma_\ell^x\sigma_{\ell+1}^x+
  \vec h\cdot\vec\sigma_\ell+
  D(\sigma_\ell^z\sigma_{\ell+1}^y-\sigma_\ell^y\sigma_{\ell+1}^z)
  \right],
  \]
  \(\vec h=((\sqrt5+5)/8,\,1/2,\,\sqrt5/2)\), \(D=\pi/20\).
- Main-text state Hamiltonian: same family with
  \(\vec h_0=(0,0,3/2)\), \(D_0=0\).
- Supplemental state Hamiltonian: same family with
  \(\vec h_0=(0,0,1/2)\), \(D_0=0\).
- Boundary condition: not explicitly stated; provisional periodic
  interpretation must remain `unknown` until independently checked.
- Generated run plan: identical formulas and couplings; local
  \(L=6\) canary, then A100 exact dense runs up to the paper's \(L=12\).

### T001 — Main Fig. 1

- Paper parameters: spin 1; constrained coordinates
  \(n_j=0\) for \(j\in\{2,4,5,6,7\}\);
  \(H=\lambda_3/2+(3\sqrt3/2)\lambda_8\).
- Generated parameters: same.
- Parameter match: `paper_exact` candidate.
- Artifact state: `final_reproduction` only after geometry identities pass.

### T002 — Main Fig. 2 left

- Paper parameters: \(L=\{6,8,10,12\}\);
  \(\beta=\{0.25,0.75,1.75\}\);
  observables \(\sigma^z_\ell\) and
  \(\sigma^z_\ell\sigma^z_{\ell+1}\);
  shells contain \(O(\sqrt d)\) consecutive \(H_\rho\) levels;
  plotted \(\Delta\) range \(0\) to about \(0.17\).
- Benchmarks: dashed curves are the commuting leaf \(\beta=0\) of \(H\);
  dotted curves use the integrable \(H_0\).
- Generated parameters: same sizes, temperatures, observables, and plotted
  range after a local shell-convention sensitivity check.
- Parameter match: `paper_exact_reconstructed_metadata`: every stated
  parameter is exact; integer shell width, edge handling, central site, and
  periodic boundary are disclosed reconstructions of omitted metadata.
- Artifact state: `final_reproduction` with source-figure-only comparison.

### T003 — Main Fig. 2 right

- Paper parameters: \(L=12\), \(\beta=0.5\), \(t\in[0,3]\);
  observables \(\sigma^x\), \(\sigma^y+0.4I\),
  \(\sigma^z-0.2I\), and \(\sigma^x\otimes\sigma^x+I\).
- Representative: minimize the paper's \(\delta_i\); use the stated
  \(\delta\)-shell for 68%/95% outlier-derived confidence bands.
- Generated parameters: identical candidate, with \(L=6\) formula/dynamics
  canary before the A100 \(L=12\) run.
- Parameter match: `paper_exact_reconstructed_metadata`: stated size,
  temperature, time range, observables, minimizer, and shell are exact;
  site/boundary and confidence-quantile implementation are disclosed.
- Artifact state: `final_reproduction`; interval comparison remains
  feature-level because only the source figure is available.

### T004–T007 — Supplemental typicality

- Paper sizes: \(L=\{6,8,10,12\}\).
- T004/T005/T006: supplemental \(H_0\), respectively
  \(\beta=0.25,0.75,1.75\), all traceless Hermitian Pauli strings on one site
  and two neighbouring sites.
- T007: \(\beta=0.25\), roles of nonintegrable \(H\) and integrable \(H_0\)
  interchanged.
- Generated parameters: same after local basis and shell checks.
- Parameter match: `paper_exact_reconstructed_metadata`, with the same
  disclosed omitted conventions as T002.
- Artifact state: `final_reproduction`.

### T008A/T008B — Fig. S5

- Paper parameters: \(L=12\), \(\beta=\{0.25,0.75,1.75\}\), energy density
  \(E/L\), entropy participation number on a logarithmic axis.
- T008A uses main-text \(H_0\); T008B uses supplemental \(H_0\).
- Generated parameters: same candidate.
- Parameter match: `paper_exact_reconstructed_metadata`.
- Artifact state: `final_reproduction`.

### T009 — Fig. S6

- Paper parameters read from the active figure:
  \(L=\{8,9,10,11,12\}\), \(\beta=\{0.25,0.75,1.75\}\), separate main-text
  \(h_{0,z}=1.5\) and supplemental \(h_{0,z}=0.5\) panels.
- Observable:
  \((\overline S_{\rm diag}^{\rm eig}-
  \overline S_{\rm diag}^{\rm mv})/L\).
- Generated parameters: same candidate.
- Parameter match: `paper_exact_reconstructed_metadata`.
- Artifact state: `final_reproduction`.

## Status Values

- `not_started`
- `spec_ready`
- `running`
- `reproduced`
- `physically_consistent`
- `algorithmically_consistent`
- `partial`
- `blocked`
- `planned_large_scale`
- `failed`

For `blocked` or `planned_large_scale` targets, add a plan document and config
path in the `Notes` column, for example:

```text
PLANNED_LARGE_SCALE_RUNS.md
config/<target>_recommended.yaml
```
