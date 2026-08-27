# Consistency Report

This file states which outputs match the paper and which do not.

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | Numeric values match reference data or paper values. |
| feature_match | 6 | Scientific or algorithmic feature matches. |
| partial_match | 0 | Some but not all checks pass. |
| input_match_only | 0 | Inputs match, outputs still differ. |
| blocked | 0 | Missing information prevents exact validation. |
| not_in_scope | 0 | Schematic, experimental, or external context. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| `T003` | Fig. 1 open-boundary phase diagram | visual_feature_reproduction | `outputs/figures/fig1_open_boundary_phase.png`, `outputs/figures/fig1_reference_comparison.png`, `outputs/checks/fig1_open_boundary_phase.json` | Bloch dotted fan, blue non-Bloch theory curve, source-table red boundary reference, shaded `C=1` region, `C=0` region, and Fig. 2 markers are rendered. | Red boundary is not yet independently regenerated from square finite-size gap extrapolation; it currently uses supplemental numerical boundary reference points. |
| `T004` | Fig. 2 square spectra and wave-packet dynamics | visual_feature_reproduction | `outputs/figures/fig2_square_dynamics.png`, `outputs/figures/fig2_reference_comparison.png`, `outputs/checks/fig2_square_dynamics.json` | Both parameter rows, low-energy spectra, and normalized `t=0,5,20` wave-packet maps are generated from the square Hamiltonian. | Source comparison is visual only; source spectra/intensity maps are not yet digitized into quantitative gates. |
| `T005` | Supplemental Fig. S2 disk finite-size gap-square fitting | visual_feature_reproduction | `outputs/figures/figs2_gap_scaling.png`, `outputs/figures/figs2_reference_comparison.png`, `outputs/checks/figs2_gap_scaling.json` | Disk gap-square samples and linear extrapolations are generated for `m=2.2000`, `2.0800`, and `2.0400`; the intercept trend matches the paper's nonzero/nonzero/near-zero interpretation. | Source comparison is visual only; larger-radius runs and digitized source-curve gates are not yet enforced. |
| `T006` | Supplemental Fig. S3 disk phase diagram | visual_feature_reproduction | `outputs/figures/figs3_disk_phase.png`, `outputs/figures/figs3_reference_comparison.png`, `outputs/checks/figs3_disk_phase.json` | Disk red numerical boundary, blue non-Bloch theory curve, gray Bloch fan, and `C=1/C=0` regions are rendered. | Red boundary uses the supplement table reference; full independent disk finite-size phase scan is not yet enforced. |
| `T002` | Fig. 3(a) cylinder phase diagram | digitized_curve_gated_feature_reproduction | `outputs/figures/fig3a_cylinder_phase.png`, `outputs/figures/fig3a_reference_comparison.png`, `outputs/checks/fig3a_cylinder_phase.json` | Phase regions, Bloch dotted lines, red non-Bloch gapless boundary, and the Fig. 3(b) star point are generated from the analytic non-Bloch cylinder band-touching boundaries. The red boundary passes digitized source-panel validation with RMSE `0.0148`. | A direct full-grid `C_y` integration gate is still pending; the source curve is used only for validation. |
| `T001` | Fig. 3(b) cylinder spectrum | numerical_feature_reproduction | `outputs/figures/first_target.png`, `outputs/figures/fig3b_reference_comparison.png`, `outputs/checks/similarity_scorecard.json`, `outputs/checks/eps_reference_points.json`, `outputs/checks/eps_point_match.json` | Complex spectrum and analytic red chiral edge trace are reproduced; EPS red-branch point matching passes. | Blue point-cloud distance and pixel-layout validation are not yet enforced as gates. |
