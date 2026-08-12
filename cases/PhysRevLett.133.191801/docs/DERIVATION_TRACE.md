# Derivation trace

## EQ001 -- axion-mediated spin potential

Starting from main-text Eq. (1), transverse spins satisfy
`sigma_I dot rhat = sigma_II dot rhat = 0`. The anisotropic tensor term then
vanishes and the mass-dependent scalar kernel is

`K_perp(m,r) = exp(-m r) (m/r^2 + 1/r^3)`.

The implementation evaluates this expression directly. Its `m -> 0` limit is
`1/r^3`; the finite-volume paper-scale path averages the same tensor kernel
over independently sampled source/sensor volume pairs.

## EQ002--EQ004 -- source and sensor response

Equation (2) is represented by the complex transverse field
`B_x + i B_y = B0 exp(-t/T_II*) exp(i 2 pi nu_II t)`. Equation (3) is the
causal first-order resonator with damping `1/T_I*`, detuning
`2 pi (nu - nu_I)`, and on-resonance gain `eta`.

For resonant exponentially decaying input, convolution of the two exponentials
gives Eq. (4): a carrier multiplied by

`2 eta B0 [exp(-t/T_I*) - exp(-t/T_II*)] / [1 - T_I*/T_II*]`.

The code uses an `expm1`-stable form and the analytic equal-time limit
proportional to `t exp(-t/T_I*)`. A separate exact linear-input stepper and RK4
solver cross-check the general Eq. (3) response.

## EQ005 -- amplification

The printed expression
`eta = 4 pi kappa_0 M_I P_0I gamma_n T_I* / 3` is implemented as a parameter
model. The feature run uses the independently printed measured value `eta=145`
because the main text does not print every factor needed to reconstruct it.

## EQ006 -- matched filter

Equation (5) is the inverse transform of a template weighted by inverse noise
PSD. For the declared white synthetic noise, normalization by
`sum(template^2)` makes the estimator unbiased. FFT correlation and direct
least squares are mathematically equivalent and are evaluated independently.

## EQ007 -- uncertainty

Independent errors add in quadrature. The printed 140 aT statistical and 45 aT
systematic components give `sqrt(140^2 + 45^2) = 147.0544117 aT`.

Every numerical equation above maps to a card in `EQUATION_CARDS.json` and a
code pointer. Unavailable supplemental geometry is never filled from pixels.
