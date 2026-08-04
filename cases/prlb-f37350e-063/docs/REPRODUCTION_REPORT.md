# Reproduction report

## Outcome

This is a broad, formula-driven reproduction of the paper rather than the former one-panel benchmark audit. Independent outputs now cover Main Figs. 1-6 and Supplemental Figs. S1-S3, with explicit partial states where the executed computation does not close the paper claim.

## Strong results

- Eq. (3) and direct PBC matrix spectra agree to `8.6e-15`.
- The corrected 2x2 stability eigenvalue agrees with direct diagonalization to `2.7e-15`; the paper's printed expression misses a factor of four.
- The static kink exponent is `-0.5045`, versus the paper's `-0.5`.
- The dynamic line-cut frequency follows the analytic dispersion with RMSE `0.00625`.
- The independently found periodic particle-hole period is `26.655`, versus caption `26.66`, with mean transformed-trajectory difference `7.67e-4`.
- Supplemental Fig. S1 reproduces all four eigenvalue curves and the coalescence-angle behavior with static residual below `2.7e-14`.

## Scientific inconsistencies found

1. The PBC stability closed form is algebraically inconsistent with the displayed 2x2 matrix unless `Lambda^2` is replaced by `4 Lambda^2`.
2. The S1 caption's critical kappa values for gamma `0.1` and `0.2` differ from independent Jacobian-zero locations by about `0.00671` and `0.00540`; gamma `0.3` agrees within `4e-5`.

## Remaining gaps

- Main Fig. 3(a): paper-resolution dynamic/static boundary.
- Main Fig. 4(a): fine multistable stripes.
- Main Fig. 4(d): all five attractors.
- Supplemental Fig. S2(b): 300 nearby trajectories.
- Fresh-context falsification review and isolated attestations for every critical target.

Therefore the lifecycle status must remain incomplete even though most visible scientific features are reproduced.
