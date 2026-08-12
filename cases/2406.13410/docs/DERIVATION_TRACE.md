# Derivation Trace

Every equation used by numerical code is named in `EQUATION_CARDS.json`.  This
document records the reasoning chain rather than treating the printed figure as
an algorithm.

## Resonance statistics — EQ001–EQ003

For an unfolded spectrum, the interval count of an independent point process
is Poisson, hence its variance equals its mean.  For GOE levels the connected
two-level correlation removes long-wavelength count fluctuations; integrating
that cluster function twice gives

`Sigma2(L) = L - 2 int_0^L (L-s) Y2(s) ds`.

The independent implementation evaluates the standard GOE kernel and also
compares against seeded finite random matrices.  Nearest-neighbor references
come directly from the unit-mean exponential and the normalized two-by-two GOE
Wigner surmise.  Neither path needs the unpublished 49 resonance positions.

## Ion energy and collision dynamics — EQ004–EQ007

A dc force displaces the ion by force balance,
`e E_dc = m_i omega_y^2 Delta y`.  At a displaced rf null the driven velocity
amplitude is linear in displacement and therefore in `E_dc`; cycle-averaged
kinetic energy is quadratic.  The appendix prints the corresponding Mathieu
coefficient EQ005 and the measured-simulation coefficient used for the energy
axis.

The paper describes, but does not publish, its Julia MD algorithm or critical
inputs (`C6`, launch radius, exact Mathieu parameters, grids, seeds).  We thus
use an independent event-driven physical reconstruction: draw thermal Li
velocities, rotate the relative velocity isotropically in the two-body COM
frame, add radial excess-micromotion impulse at a random rf phase, and repeat to
stationarity.  The collision map

`v_i' = V + m_a/(m_i+m_a) R(v_i-v_a)`

preserves momentum and elastic kinetic energy exactly.  This is sufficient to
test the quadratic median-energy law and radial/axial anisotropy, but it is
explicitly `reconstructed`, not paper-exact author MD.

## Density and classical loss — EQ008–EQ009

The printed Gaussian width gives
`FWHM = 2 sqrt(2 ln 2) sigma = 19.31 um`, agreeing with `19.4(8) um`.
The local density enters the three-body rate quadratically.  The quoted `k3`
is normalized at 10 mK, so the numerical form keeps that normalization explicit
before applying `(E0+DeltaE)^(-3/4)`.  Exponential decay over the printed 200 ms
converts the rate to survival.  Missing figure-specific peak density affects
absolute height, not the independently testable shape and exponents.

## Polarization scattering — EQ010–EQ013

Starting from

`[-hbar^2/(2mu) d2/dr2 + hbar^2 l(l+1)/(2mu r2) - C4/r4]u = E u`,

define `R*=sqrt(2mu C4/hbar^2)`, `x=r/R*`, and `E_s=hbar^2/(2mu R*^2)`.
This yields EQ010.  The effective barrier
`l(l+1)/x^2 - 1/x^4` is maximal at
`x_b^2=2/[l(l+1)]`, so `E_l/E_s=[l(l+1)]^2/4`, giving the printed p/d/f
guides `1, 9, 36`.

An incoming-only WKB boundary at small radius represents unit short-range
reaction probability.  Matching the propagated complex solution to incoming
and outgoing Riccati-Hankel waves at large radius gives `S_l`; missing flux
`1-|S_l|^2` is the quantum-defect coupling `C_l^-2`.  The same probabilities
give the universal capture rate after partial-wave degeneracy summation.  A
separate classical-barrier approximation is retained as an independent
cross-check, never as source-pixel fitting.

## Resonant recombination and averaging — EQ014–EQ017

EQ014 and magnetic detuning EQ015 are printed.  We substitute
`Gamma=Gamma_m C_l^-2` and the independently computed universal capture rate.
The authors specify that the correct energy is the three-body relative energy,
not the laboratory ion energy.  For two sampled atoms and one sampled ion we
therefore subtract their total center-of-mass velocity before summing kinetic
energies.  Monte Carlo averages the Lorentzian rate, followed by exponential
survival.

Substituting the threshold law `C_l^-2 ~ k^(2l+1)` into EQ014 yields the three
printed asymptotes in EQ017.  These slopes, unitarity bounds, barrier positions,
the low-energy suppression of the f wave, and an intermediate-energy f-wave
maximum are acceptance tests.  Missing f-wave `Gamma_m`, bare `B_res`, exact
atom-dimer polarization scale, and author velocity arrays remain reconstructed
parameters; they cannot be silently optimized against source pixels.

For Fig. 6(h), EQ018 follows the explicitly printed `4.4(4) mG/microkelvin`
linear fit rather than substituting reconstructed model peaks for unavailable
experimental fit points.  The inferred `320.0 G` intercept reproduces the
textual `321.53(3) G` anchor at `x=1.81` within its stated precision; it is
recorded as reconstructed because the intercept itself is not tabulated.
