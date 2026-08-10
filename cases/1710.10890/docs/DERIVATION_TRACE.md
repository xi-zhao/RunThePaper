# Derivation Trace

## Formula Lane Rule

Only equations listed in `EQUATION_CARDS.json` may feed the isolated runner.
The main-paper PDFs, source figures, and comparison crops are outside that
runner. The scattering-length interpolant is a transparent reconstruction from
published table entries, not a fit to Fig. 1 pixels.

## EQ001 — Scattering-length parameter lane

The later primary-source table gives three independent coupled-channel values
for each `a_ij` at 56.230, 56.453, and 56.639 G. A centered quadratic Lagrange
interpolant passes exactly through those rows. Its extrapolation is used only to
display the wider Fig. 1(a) context; claim checks are restricted to the table
interval and to the independently printed zero crossing near 56.85 G.

## EQ002 — Effective mean-field attraction and density locking

Writing the mean-field quadratic form in hard/soft density coordinates shows
that the hard mode is minimized at
`n1/n2=sqrt(a22/a11)`. Along that ray, the residual attraction is controlled by
`delta_a=a12+sqrt(a11*a22)`. The sign change separates the mean-field gas from
the LHY-stabilized regime.

## EQ003 — LHY-stabilized coupled GPE

Functional differentiation of the printed GP plus LHY energy gives the two
chemical potentials. Near collapse, `g12^2=g11*g22` removes higher-order
`delta_g` corrections and yields the local LHY derivative used by the paper.
No author implementation is consulted.

## EQ004 — Saturation densities and healing length

Setting the pressure of the locked mixture to zero balances the attractive
`n^2` term against the repulsive `n^(5/2)` LHY term. This gives the two
saturation densities. Rescaling the kinetic term to the same interaction unit
gives `xi(B)`.

## EQ005 — Universal dimensionless droplet equation

Substitution `Psi_i=sqrt(n_i0) phi` and `r=xi*r_tilde` reduces the stationary
problem to

`-laplacian(phi)/2 - 3 phi^3 + 5 phi^4/2 - mu phi = 0`.

The runner solves its spherical boundary-value form with regularity at the
origin and exponential decay at large radius. Direct quadrature recovers the
Petrov fold `N_tilde=18.65` at `mu≈-0.061`.

## EQ006 — Mapping to `N_c` and `sigma`

Each physical species number is `N_i=n_i0*xi^3*N_tilde`; summing the two gives
the phase boundary. Petrov's metastability fold uses 18.65, while zero total
energy gives the stable threshold 22.55. The baseline maps the spherical
profile to one-axis RMS `sqrt(<r^2>/3)*xi`; the paper does not state the
theory-density fitting functional used to compare with its experimental
1/e² Gaussian width. That missing equivalence is why the stable T005 ordering
difference is inconclusive.

## EQ007 — Optical levitation

The supplement specifies `z0(t)` and the period average of a moving Gaussian.
The unknown overall optical amplitude cancels as a free fit parameter: it is
fixed by the stated levitation condition `|dV/dz|=mg` at the atom position.
Differentiating the resulting potential gives its curvature. Fig. S1(c) signs
the displayed frequency by the force gradient, `-V''`, so the reproduction
uses `sgn(-V'')*sqrt(|V''|/m)/(2*pi)`. This gives the source panel's
positive-left/negative-right branch orientation without changing the
potential itself.

## EQ008 — Supplementary expansion proxy

For a Thomas--Fermi condensate the GPE continuity and Euler equations close on
scale factors `b_i(t)`. The stated trap frequencies and scattering length set
the initial TF radius, and the post-release equations determine the free and
12 Hz confined curves. The supplement does not state the atom number of this
calibration cloud, so the runner uses the paper's stated preparation maximum
`4e5`; the result remains a proxy and cannot be called paper-exact.

## EQ009 — Three-dimensional preparation, propagation, and observables

The supplement gives a reproducible initial-state *procedure*, even though it
does not publish an initial array: solve the single-component state-2 GPE in the
experimental harmonic trap, then apply an instantaneous 50/50 transfer. Main
Fig. 4 subsequently evolves the two coupled GPEs with the local LHY derivative
from EQ003 and no losses. Supplement Fig. S2 instead retains the single
component and evolves it in free space or a 12 Hz vertical harmonic potential.

For a time-independent step, symmetric Strang splitting gives

`exp(-i H dt/hbar) = exp(-i T dt/(2 hbar)) exp(-i U dt/hbar) exp(-i T dt/(2 hbar)) + O(dt^3)`.

The kinetic exponent is diagonal in Fourier space and the external,
mean-field, and LHY terms are diagonal in real space. Imaginary-time evolution
uses the analogous real exponent with renormalization to the configured atom
number.

The main-text 1/e² half-width of a Gaussian obeys `sigma_i=2*RMS_i`, hence the
reported Main Fig. 4 observable is `2*sqrt(RMS_x*RMS_z)`. For the 3D
inverted-parabola density used by Supplement Fig. S2,
`<z²>=R_z²/7`, so its moment-equivalent vertical TF radius is
`R_z=sqrt(7)*RMS_z`.

The code independently differentiates the LHY energy density by finite
differences, checks radial solutions with a Pohozaev scaling identity, compares
512³ trajectories to both 640³ and half-step runs, and rejects FFT trajectories
with significant outer-box mass. These gates establish implementation and
numerical validity; the missing Fig. 4/S2 atom numbers still block paper-exact
agreement.
