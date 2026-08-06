# Fig. 3(g) / Fig. S2 evidence discrepancy

## Finding

The dash-dotted lower branch in Fig. 3(g) is nonlinearly unstable, so its visual
classification is defensible. However, the positive-Bogoliubov-eigenvalue
explanation stated in the paper does not follow for the fixed point that matches
the plotted ordinate when the printed equations and parameters are evaluated.

This is a narrow methodological discrepancy. It is not evidence against the
paper's upper stable branch or its main two-photon-loss stabilization mechanism.
The conclusion is confirmed against the published main article and the
equations printed in the accessible arXiv v1 supplement; a change in the formal
supplement version cannot yet be excluded.

## Independent calculation at $\lambda/\omega_c=1.25$

The parameters are $\omega_a=\omega_c=1$, $\kappa_1=0.4$, and
$\kappa_2=0.2$.

| Fixed-point family | $\langle a^\dagger a\rangle/N$ | Largest non-neutral real part | Result | Relation to Fig. 3(g) |
| --- | ---: | ---: | --- | --- |
| coherent low | 0.185381 | +1.332995 | linearly unstable | not plotted |
| squeezed low | 0.193901 | +1.217871 | linearly unstable | not plotted |
| squeezed high | 3.304133 | -0.020170, plus two zero modes | linearly marginal | matches the dash-dotted lower curve |
| coherent high | 10.394295 | -0.000481 | stable | matches the solid upper curve |

The squeezed-high solution has residual below $10^{-10}$, unit normalized spin
length, and positive bosonic covariance margin. Jacobians on the physical
eight-real-variable space, with finite-difference steps from $10^{-4}$ through
$10^{-8}$, show no positive eigenvalue.

One zero mode is associated with the spin-length constraint. Along the photon
first-moment mode, the printed equation gives

$$
\dot r=2\kappa_2 r^3+O(r^5)=0.4r^3+O(r^5),
$$

so a small perturbation grows: the branch is nonlinearly unstable even though
its Bogoliubov spectrum has no positive eigenvalue.

## Likely source of the mismatch

The plotted squeezed-high photon number may have been paired with the positive
eigenvalue of the distinct squeezed-low root. Another possibility is that a
nonlinear instability was described as a positive-eigenvalue linear result.
The machine-readable branch audit is in
[`figS2_science.json`](../outputs/checks/figS2_science.json), and the underlying
generated values are summarized in
[`analytic_summary.json`](../outputs/data/analytic_summary.json).

Until an independent review or author clarification resolves the provenance of
the stated spectrum, this target remains valid-with-discrepancy rather than
complete.
