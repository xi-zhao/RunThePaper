# Target Ledger

Only `numeric_reproduction` figures enter this ledger. Schematic and
experimental figures are recorded in `FIGURE_CLASSIFICATION.md` and excluded
from executable reproduction.

Formula gate rule: a target can only start implementation if all required
equation cards have `numeric_gate = true` in
`outputs/checks/formula_verification.json`.

Comparison rule: acceptance is based on numerical data, physical features, and
digitized original-figure references. The digitized references come from the
paper EPS/PNG figure sources; they are stronger than visual-only comparison but
still weaker than author-provided plotting data.

W1 authority uses the scorecard IDs, not the older section numbering that once
assigned a new target to every script. Atomic item counts are T001=4, T002=6,
T003=1, T004=3, T005=8, T006=1, T007=1, T008=1.

## T001: Fig. 2(a-c) Open-Chain Spectrum

- Scope class: `numeric_reproduction`
- Status: `digitized_curve_match`
- Source figure: Fig. 2, label `spectsmall`
- Source files: `abssmall.eps`, `realsmall.eps`, `imaginesmall.eps`
- Model: non-Hermitian SSH, `t3 = 0`
- Parameters: `L=40`, `t2=1`, `gamma=4/3`, `t1 in [-3,3]`
- Boundary condition: open chain
- Output data: `outputs/data/fig2_open_spectrum.csv`
- Output figure: `outputs/figures/fig2_open_spectrum.png`
- Output checks:
  - `outputs/checks/fig2_open_spectrum.json`
  - `outputs/checks/all_digitized_curves.json`
- Digitized reference:
  - `internal-reference-curves/fig2_abssmall_digitized.csv`
  - `internal-reference-curves/fig2_realsmall_digitized.csv`
  - `internal-reference-curves/fig2_imaginesmall_digitized.csv`
- Expected physics:
  - Eigenvalues come in approximately `(E, -E)` pairs from chiral symmetry.
  - Two near-zero modes appear for `|t1| < sqrt(t2^2 + (gamma/2)^2)`.
  - The transition is near `|t1| = 1.20185`, not at the Bloch gap closing
    values `1/3` or `5/3`.
- Current evidence:
  - `outputs/checks/fig2_open_spectrum.json` passes structural checks.
  - `outputs/data/fig2_open_spectrum.csv` contains regenerated spectrum data.
  - `outputs/figures/fig2_open_spectrum.png` redraws the spectrum panels.
  - Fig. 2(a-c) panels now have digitized EPS/PNG reference checks; T001's
    target-level mismatch count in `all_digitized_curves.json` is `0`.
- Acceptance basis: digitized figure-source agreement, spectral symmetry,
  zero-mode interval, finite-size gap behavior, and transition location.

## T001 (continued): Fig. 2(d) Boundary Perturbation

- Scope class: `numeric_reproduction`
- Status: `digitized_curve_match`
- Difference from T001: replace the leftmost intracell `t1` by `t1 - 0.8`.
- Expected physics: extra nonzero modes may appear, but the zero modes remain.
- Required formula cards: `EQC003`, `EQC005`
- Output data: `outputs/data/fig2_boundary_perturbation.csv`
- Output figure: `outputs/figures/fig2_boundary_perturbation.png`
- Output checks:
  - `outputs/checks/fig2_boundary_perturbation.json`
  - `outputs/checks/all_digitized_curves.json`
- Digitized reference:
  - `internal-reference-curves/fig2_absdisorder_digitized.csv`
- Current evidence:
  - Robust zero modes survive inside the verified transition interval.
  - Zero modes are absent outside the transition interval.
  - Additional nonzero near-zero modes appear, matching the paper caption.
  - Fig. 2(d) has a digitized EPS reference check with mismatch count `0`.

## T002: Fig. 3 Generalized Brillouin Zone and Skin Effect

- Scope class: `numeric_reproduction`
- Status: `digitized_curve_match`
- Expected ingredients: beta roots, `|beta_1|=|beta_2|`, eigenstate profiles.
- Required formula cards: `EQC003`, `EQC006`, `EQC007`
- Parameters: `L=40`, `t1=1`, `t2=1`, `gamma=4/3`; transition comparison
  uses `t1=sqrt(t2^2+(gamma/2)^2)`.
- Output data:
  - `outputs/data/fig3_beta_roots.csv`
  - `outputs/data/fig3_cbeta.csv`
  - `outputs/data/fig3_profiles.csv`
- Output figure: `outputs/figures/fig3_beta_skin.png`
- Output checks:
  - `outputs/checks/fig3_beta_skin.json`
  - `outputs/checks/all_digitized_curves.json`
- Digitized reference:
  - `internal-reference-curves/fig3_absbeta_digitized.csv`
  - `internal-reference-curves/fig3_cbeta_digitized.csv`
  - `internal-reference-curves/fig3_profile_digitized.csv`
- Current evidence:
  - Formula gate is open for all required formula cards.
  - `C_beta` radius for `t1=1` is `sqrt(0.2)`.
  - `|beta_1|=|beta_2|` holds on the bulk-energy branch.
  - Zero mode and selected bulk right eigenvectors are left-localized.
  - Published EPS/PNG panels have been digitized for beta-root, `C_beta`, and
    profile reference checks; target-level mismatch count is `0`.
- Acceptance basis: digitized figure-source agreement, beta-root equal-modulus
  branch, `C_beta` radius, zero-mode profile ratio, and bulk-state left
  localization.

## T003: Fig. 4 Non-Bloch Winding Number

- Scope class: `numeric_reproduction`
- Status: `digitized_curve_match`
- Expected ingredients: `H(beta)`, biorthogonal eigenvectors, `Q(beta)`,
  winding along `C_beta`.
- Required formula cards: `EQC006`, `EQC007`, `EQC009`
- Parameters: `t2=1`, `gamma=4/3`, `N_beta=150`, `t1 in [-3,3]`
- Output data: `outputs/data/fig4_winding.csv`
- Output figure: `outputs/figures/fig4_winding.png`
- Output checks:
  - `outputs/checks/fig4_winding.json`
  - `outputs/checks/fig4_digitized_curve.json`
- Digitized reference:
  - `internal-reference-curves/fig4_winding_digitized_markers.csv`
  - `internal-reference-curves/fig4_winding_digitized_step_vertices.csv`
- Current evidence:
  - Formula gate is open for all required formula cards.
  - Winding is `W=1` for `|t1| < sqrt(t2^2 + (gamma/2)^2)` and `W=0`
    outside, away from the transition grid tolerance.
  - Published EPS has been rendered as `internal-source-renders/invariant_source.png`
    for visual reference.
  - The original EPS vector marker and step path have been digitized. All 23
    marker values match the generated winding CSV; the max transition-vertex
    `t1` error is `0.0082`, within the generated `0.02` grid tolerance.
- Acceptance basis: digitized EPS curve agreement, winding plateau values, and
  transition location, not pixel similarity to the rendered EPS.

## T004: Fig. 5 Nonzero `t3`

- Scope class: `numeric_reproduction`
- Status: `digitized_curve_match`
- Source figure: Fig. 5, label `t3`
- Source files: `t3spectrum.eps`, `t3betacurve.eps`
- Model: non-Hermitian SSH with nonzero `t3`
- Required formula cards: `EQC001`, `EQC009`, `EQC010`
- Parameters: `L=100`, `t2=1`, `gamma=4/3`, `t3=1/5`,
  `N_beta=200`, `t1 in [-3,3]`; `C_beta` panel uses `t1=1.1`.
- Output data:
  - `outputs/data/fig5_t3_spectrum.csv`
  - `outputs/data/fig5_t3_winding.csv`
  - `outputs/data/fig5_t3_cbeta.csv`
- Output figure: `outputs/figures/fig5_t3.png`
- Output checks:
  - `outputs/checks/fig5_t3.json`
  - `outputs/checks/all_digitized_curves.json`
- Digitized reference:
  - `internal-reference-curves/fig5_t3_spectrum_digitized.csv`
  - `internal-reference-curves/fig5_t3_winding_digitized.csv`
  - `internal-reference-curves/fig5_t3_cbeta_digitized.csv`
- Current evidence:
  - The nonzero-`t3` beta quartic is source-verified and symbolically checked.
  - The `E=0` beta-root ordering gives transition points
    `t1 = -1.562` and `t1 = 1.562`, matching the caption value `~ +/-1.56`.
  - `W=1` inside the transition interval and `W=0` outside, with no mismatch
    away from the transition tolerance.
  - Reconstructed `C_beta` for `t1=1.1` is inside the unit circle but not a
    circle; its radius range is about `0.492` to `0.776`.
  - Fig. 5 spectrum, winding, and `C_beta` panels have digitized EPS reference
    checks with target-level mismatch count `0`.
  - The visible spectrum curves are independently generated from open-chain
    `|E|` levels. The `branch_id` field labels the ordered absolute-energy
    level across `t1`; original EPS paths are only reference comparators.
- Acceptance basis: beta-root transition location, winding plateau values,
  middle-root pairing error, `C_beta` radius features, and digitized
  figure-source agreement as a reference comparator.

## T005 (part A): Supplemental Fig. 6 Complex-Plane Spectra

- Scope class: `numeric_reproduction`
- Status: `digitized_curve_match`
- Model: `t3=0` non-Hermitian SSH spectra in the complex plane.
- Required formula cards: `EQC006`, `EQC007`, `EQC008`
- Parameters: `L=120`, `t2=1`, `gamma=4/3`, `t1 in {0.2, 0.6, 1.0}`.
- Output data:
  - `outputs/data/supplemental_fig1_theory_complex_spectra.csv`
  - `outputs/data/supplemental_fig1_open_chain_complex_spectra.csv`
- Output figure: `outputs/figures/supplemental_fig1_complex_spectra.png`
- Output checks:
  - `outputs/checks/supplemental_fig1_complex_spectra.json`
  - `outputs/checks/all_digitized_curves.json`
- Digitized reference:
  - `internal-reference-curves/supplemental_fig1_theory_complex_digitized.csv`
  - `internal-reference-curves/supplemental_fig1_open_complex_digitized.csv`
- Current evidence:
  - All three `t1` cases are present.
  - Finite open-chain spectra lie close to the theoretical non-Bloch spectrum;
    p95 nearest-curve distances are below `0.006`.
  - Representative supplemental complex-spectrum panels have digitized EPS
    reference checks with mismatch count `0`.
- Acceptance basis: digitized figure-source agreement and complex-spectrum
  curve agreement in data space, not visual overlay alone.

## T005 (part B): Supplemental Fig. 7 Large `gamma`

- Scope class: `numeric_reproduction`
- Status: `digitized_curve_match`
- Model: `t3=0` non-Hermitian SSH with `|t2| < |gamma|/2`.
- Required formula cards: `EQC003`, `EQC005`, `EQC006`, `EQC007`, `EQC009`
- Parameters: `L=40`, `t2=1`, `gamma=2.4`, `N_beta=150`,
  `t1 in [-3,3]`.
- Output data:
  - `outputs/data/supplemental_fig2_gamma24_spectrum.csv`
  - `outputs/data/supplemental_fig2_gamma24_winding.csv`
- Output figure: `outputs/figures/supplemental_fig2_gamma24.png`
- Output checks:
  - `outputs/checks/supplemental_fig2_gamma24.json`
  - `outputs/checks/all_digitized_curves.json`
- Digitized reference:
  - `internal-reference-curves/supplemental_fig2_spectrum_digitized.csv`
  - `internal-reference-curves/supplemental_fig2_winding_digitized.csv`
- Current evidence:
  - The four transition points appear at
    `|t1| = 0.6633249580710799` and `|t1| = 1.5620499351813308`.
  - `W=0` in the center, `W=1` in the two intermediate regions, and `W=0`
    outside; mismatch count away from transitions is `0`.
  - Supplemental Fig. 2 spectrum and winding panels have digitized EPS/PNG
    reference checks with mismatch count `0`.
- Acceptance basis: digitized figure-source agreement, four transition
  locations, and winding plateau pattern.

## T006: Zero-mode Endpoint Migration Claim — Uncovered

- Source: main PDF p. 4, paragraph beginning “Quantitatively, 2W counts...”.
- Direct cause: no artifact jointly checks the two zero modes' left/right
  endpoint weights in all three printed `t1` intervals.
- Root cause: the historical figure-centered inventory omitted this independent
  prose claim.
- Code fault: not excluded; adjacent spectrum/profile code has never been
  exercised against the interval-by-interval endpoint allocation.
- Next discriminating test: evaluate one paper-exact `t1` in each interval,
  compute normalized left/right weights for both zero modes, and compare them
  with the analytic beta-root localization directions.
- Expected evidence: `outputs/checks/T006_zero_mode_endpoint_migration.json`.

## T007: Multiband Winding Sum — Uncovered

- Source: main PDF p. 4, final paragraph before Conclusions.
- Direct cause: no block-diagonal multiband example evaluates each paired-band
  winding and verifies `W=sum_l W^(l)`.
- Root cause: the earlier case stopped at displayed two-band results.
- Code fault: not excluded; the current two-band invariant has not been tested
  for band-pairing and gauge behavior in a multiband model.
- Next discriminating test: combine two SSH blocks with known windings and
  compare the full invariant with their independently evaluated sum.
- Expected evidence: `outputs/checks/T007_multiband_winding_sum.json`.

## T008: Correction to Ref. 49 — Source-blocked

- Source: main PDF p. 7, footnote [92].
- Direct cause: Ref. 49's full model convention and evidentiary context are not
  frozen in this case.
- Root cause: the historical review process treated the related-work footnote
  as context instead of a falsifiable quantitative correction.
- Code fault: not applicable until the cited scientific target is fixed;
  source pixels cannot replace the missing model definition.
- Next discriminating test: freeze Ref. 49, independently reconstruct its
  zero-mode interval, and compare it with both papers' statements.
- Expected evidence: `outputs/checks/T008_ref49_zero_mode_correction.json`.
