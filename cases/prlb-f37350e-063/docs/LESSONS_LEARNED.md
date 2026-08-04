# Lessons learned

1. A strongly non-normal nonlinear boundary problem may have exact but unstable roots. Static-state reproduction needs an attractor-selection rule before root refinement.
2. Displayed matrices should be diagonalized independently even when a closed form is printed. Here that exposed a missing factor of four.
3. Caption critical values are hypotheses, not ground truth. Independent Jacobian-zero searches found material offsets for two S1 curves.
4. Particle-hole symmetry can require a fractional time shift and a global phase. Integer-sample comparison falsely makes a correct trajectory look inaccurate.
5. Lyapunov calculations should integrate state and tangent equations with the same RK stages; a post-step Jacobian approximation can shift exponents.
6. Broad phase features and fine multistable stripes are different targets. A coarse scan must not be promoted to paper-exact coverage.
7. Source figures are useful after scientific data freeze for RenderContract work, but must remain outside numerical parameter selection and array generation.

## New Failure Modes

- `exact_root_not_physical_attractor`
- `printed_closed_form_disagrees_with_displayed_matrix`
- `caption_critical_value_not_jacobian_zero`
- `integer_delay_breaks_continuous_symmetry_check`
- `coarse_basin_scan_promoted_to_fine_phase_map`

## Reusable Checks Or Tools

- direct matrix-versus-closed-form eigenvalue comparison;
- scalar-versus-vectorized RHS comparison;
- exact Jacobian versus finite differences;
- shared-stage state/tangent RK4 regression;
- source-free isolated run attestation;
- post-freeze scientific-region pixel comparison.
