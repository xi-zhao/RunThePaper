# Target Ledger

One target corresponds to one paper figure. The original reduced run remains as
historical evidence; current status is determined by the paper-scale workflow.

| Target ID | Paper item | Type | Formula dependencies | Formula gate | Status | Data output | Figure output | Check output | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Fig. 3 | numeric reproduction | EQC001–EQC006 | passed | paper_scale_feature_match | `outputs/paper_exact/data/paper_{ed_histograms,fig34_theory,profiles,scaling}.*` | `outputs/paper_exact/figures/fig3_paper_exact.png` | `outputs/checks/paper_scientific_similarity.json` | Paper ED scale; all four panels; strict pixel identity remains open. |
| T002 | Fig. 4 | numeric reproduction | EQC001–EQC003, EQC005–EQC007 | passed | paper_scale_feature_match | `outputs/paper_exact/data/paper_{ed_histograms,fig34_theory}.npz` | `outputs/paper_exact/figures/fig4_paper_exact.png` | `outputs/checks/paper_scientific_similarity.json` | Paper ED scale and winding-sector labels. |
| T003 | Fig. 5 | numeric reproduction | EQC001–EQC004, EQC006, EQC008 | passed | paper_scale_feature_match | `outputs/paper_exact/data/paper_{fig5_contours,alpha}.*` | `outputs/paper_exact/figures/fig5_paper_exact.png` | `outputs/checks/paper_scientific_similarity.json` | Exact W list/range and reproduced `W_c=2.1`. |
| T004 | Fig. S1 | numeric reproduction | EQC001–EQC006, EQC009 | passed | reduced_scale_feature_match | `outputs/supplement_feature/data/supplement_offdiag_{grid,profiles}.csv` | `outputs/supplement_feature/figures/figs1_reproduction.png` | `outputs/supplement_feature/checks/supplement_feature_checks.json` | Transfer/ED hopping orientation corrected and protected by row-residual tests; unpublished grid/windows cap fidelity. |
| T005 | Fig. S2 | numeric reproduction | EQC001–EQC006, EQC009 | passed | reduced_scale_feature_match | `outputs/supplement_feature/data/supplement_quasiperiodic_{grid,profiles}.csv` | `outputs/supplement_feature/figures/figs2_reproduction.png` | `outputs/supplement_feature/checks/supplement_feature_checks.json` | Transfer/ED hopping orientation corrected and protected by row-residual tests; unpublished grid/windows cap fidelity. |
| T006 | Main-text one-way limit | quantitative reproduction | EQC001, EQC004, EQC010 | passed | reproduced | `outputs/data/unidirectional_density.csv` | not applicable | `outputs/checks/supplement_additional_numerics.json` | Exact triangular-matrix identity and independent finite eigenspectrum check. |
| T007 | Published Fig. S3 | numeric reproduction | EQC002–EQC004, EQC011 | passed | compute_blocked_after_pilot | `outputs/data/supplement_s3_precision_pilot.csv` | `outputs/figures/figs3_precision_pilot.png` | `outputs/checks/supplement_compute_benchmark.json` | Full paper-scale code exists; isolated pilot measures the `L=1000 x 1600` multiprecision boundary. |
| T008 | Published Fig. S4 | numeric reproduction | EQC003, EQC012 | passed | attempted_not_reproduced_pending_review | `outputs/data/supplement_s4_{gap_scaling,protocol_sensitivity}.csv` | `outputs/figures/figs4_gap_scaling.png` | `outputs/checks/supplement_additional_numerics.json` | Full reported size/energy grid plus 18-protocol sensitivity sweep run; 0/18 supports the exponential feature, pending fresh review. |

## T006 Parameter Card — unidirectional density limit

- Paper class: only `t1` or only `t-1` nonzero under OBC; onsite values follow
  an arbitrary distribution `rho_w`.
- Generated representative: `L=128`, 32 independently seeded Uniform[-0.8,0.8]
  samples, one-way hopping 1.
- Parameter match: `paper_exact` at the paper's declared equivalence-class level;
  triangularity proves the identity for every onsite sequence.
- Source pixels/author data/code: not used.

## T007 Parameter Card — Published Fig. S3

- Paper: `L=1000`, 1600 realizations, `E={-0.72,3.20}`,
  precisions `{64,112,160,208}` bits, 256-bit ED reference.
- Generated pilot: all paper energies/precisions at `L=12`, 2 realizations.
- Parameter match: `reduced_scale`; artifact stage: `exploratory`.
- Paper-scale path: same config object accepts the published length/ensemble;
  a measured cubic/ensemble projection records why it was not launched locally.
  The required 112–256-bit dense eigensolving is not a native A100 FP32/FP64
  workload; even an optimistic idealized 50x speedup leaves about 73 days.

## T008 Parameter Card — Published Fig. S4

- Paper: `E0=-0.9328+0.2210i`, `L={50,...,400}`, `L_ref=1000`.
- Generated: same reported values, a frozen 64-realization/`qr_interval=1`
  baseline, plus 18 predeclared combinations of 16/64/128 realizations, three
  seeds, and `qr_interval={1,4}`.
- Parameter match: `paper_subset`; the paper omits ensemble size, realization,
  averaging order, and QR interval.
- Evidence: both exponential and power-law fit residuals are reported; 0/18
  protocols support the frozen exponential feature threshold, so the generated
  non-match is retained for independent adjudication.

## T001 Parameter Card — Fig. 3

- Original model: `M=2`, `W=0.8`, `t2=0.5`, `t1=1.5`, `t-1=1`, `t-2=1`.
- Paper ED: `L=1000`, 3200 disorder realizations.
- Paper markers: `E=-0.6` and `E=-1.05+0.32i`.
- Paper fit exponents: `-1.104` at `E=-0.6`; `-1.008` at the complex point.
- Unknown: transfer length, grid, seeds, density smoothing, profile windows.
- Current run: paper ED scale, exact model/markers, high-resolution LE grid, and
  one shared asymptotic fit window `L>=400`.
- Parameter match: `paper_reported_plus_documented_inference`.
- Artifact stage: `paper_matched_reproduction`.
- Reference comparison: paper values, feature-level density support, and strict
  source-image pixel QA.
- Generated-data provenance: `independent_numerics`.
- Panel coverage: (a–d) independently reproduced; microscopic profile identity is
  unavailable because seeds/windows are not published.

## T002 Parameter Card — Fig. 4

- Original model: same parameters as Fig. 3 under PBC.
- Paper labels winding values `-1,+1,-1` in the three spectral holes.
- Unknown: grid, transfer length, seeds, and smoothing.
- Current run: same Hamiltonian/disorder at `L=1000 × 3200`; winding is checked by
  both `M-n_P` and a direct twisted determinant.
- Parameter match: `paper_reported_plus_documented_inference`.
- Artifact stage: `paper_matched_reproduction`.
- Reference comparison: `analytic_reference` for integer winding and
  `source_figure_only` for density layout.
- Generated-data provenance: `independent_numerics`.
- Panel coverage: (a) reproduced, (b) reproduced.

## T003 Parameter Card — Fig. 5

- Original contour strengths: `W={0.4,0.8,1.2,1.6,2.0}`.
- Paper transition: `W_c≈2.1`; alpha is shown on `W in [0,3]`.
- Unknown: alpha ensemble/grid, seeds, transfer length, and threshold rule.
- Current run: exact contour W list/range and a 31-point alpha scan with `L=1000`
  ED samples classified by Lyapunov exponents.
- Parameter match: `paper_reported_plus_documented_inference`.
- Artifact stage: `paper_matched_reproduction`.
- Reference comparison: `analytic_reference` for `W_c≈2.1` and a structured
  feature contract for shrinking contours.
- Generated-data provenance: `independent_numerics`.
- Panel coverage: (a) reproduced, (b) reproduced.

## Status Values

- `not_started`
- `spec_ready`
- `running`
- `reproduced`
- `physically_consistent`
- `paper_scale_feature_match`
- `algorithmically_consistent`
- `partial`
- `blocked`
- `planned_large_scale`
- `failed`
