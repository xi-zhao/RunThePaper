# Derivation trace

## EQ001 -- effective three-species Hamiltonian

Main Eq. (1) contains free holes, excitons, and trions plus the conversion
`h+x <-> t`.  The printed mass relation gives `m_x=2 m_h`, `m_t=3 m_h`.
Chemical equilibrium cancels all chemical potentials in the on-shell reaction
constraint.

## EQ002 -- scattering amplitude

The supplement first derives `f(E)=-2 m_red T(E)` and then a logarithmic
two-dimensional T matrix.  Its logarithm acquires `+i*pi` in the continuum.
The caption, the first T-matrix expression, and the subsequently printed pole
denominator do not share a single sign convention for negative `E_t^0`.
T001 therefore evaluates both explicitly labelled conventions and cannot be
paper-exact without guessing a linewidth or sign from the plotted pixels.

## EQ003 -- thermodynamic closure

The production lane follows the paper's explicit parameterization: the printed
hole Fermi energy fixes `mu_h`, the printed free-exciton density fixes `mu_x`,
and `mu_t=mu_h+mu_x`.  For the ideal two-dimensional gases,

`n_F=m kT/(2*pi*hbar^2) log(1+exp(mu/kT))`,

`n_B=-m kT/(2*pi*hbar^2) log(1-exp(mu/kT))`.

The analytic inverse of the Bose expression fixes `mu_x`; `n_h` and `n_t` then
follow from the Fermi expression.  A second sensitivity lane instead conserves
total hole/exciton constituents, because the manuscript does not explicitly
state which density interpretation its production code used.  Neither lane is
selected by fitting the paper curves.

## EQ004 -- angular-harmonic Boltzmann reduction

For isotropic linear response write each departure as
`phi_i(q,theta)=u_i(q) cos(theta)`.  With quadratic dispersions the reaction
delta function is integrated analytically.  For fixed hole/exciton radii,

`F/E_F=(2/3)p^2+(1/6)k^2-(2/3)pk cos(phi)-Delta/E_F`.

The two roots exist only when `|cos(phi)|<1`; their Jacobian is
`2/[E_F (2pk/3) sqrt(1-cos(phi)^2)]`.  Linear interpolation maps the on-shell
trion radius back to its radial grid.  This reduces a two-dimensional angular
problem to three coupled one-dimensional radial fields without sampling a
source curve.

The source additionally retains selected `O(g^4)` feedback terms.  The first
implementation solves the complete printed `O(g^2)` collision equations and
uses a separately declared iterative feedback channel for the higher-order
comparison.  This distinction is retained in T009.

## EQ005 -- resonance and self-energy

At the hole Fermi surface the angularly integrated phase space peaks when hole
and trion Fermi radii coincide.  Substituting `m_t=3m_h` into Main Eq. (3)
gives `Delta_star=(2/3)mu_h`.  The collision prefactor in the paper's units
reduces to `6 t^2/|E_t^0|`, which is converted from meV to inverse ps by
division by `hbar`.

## EQ006 -- currents

The radial solutions are integrated with their bare velocities according to
the supplement conductivity definition.  Hole conductivity is normalized by
`sigma_0^h=mu_F e^2 tau_0/(2*pi*hbar^2)`; neutral-particle drag is reported in
the same normalization, exactly as in the figures.

## EQ007 -- independent Kubo lane

The retarded self-energy in Supplement Eq. (39) is evaluated with the printed
finite lifetime.  Supplement Eq. (40) then reduces the dc conductivity to a
one-dimensional energy quadrature.  It is coded independently of the
Boltzmann matrix assembly so that disagreement can expose a reproduction
defect rather than being hidden by shared code.

## EQ008 -- three-fluid ac response

The printed coupled velocity equations form a complex `3x3` linear system for
each frequency.  Solving that system is algebraically equivalent to
Supplement Eqs. (41)--(43) and provides an independent direct-matrix check.
The reported relaxation times and three drag coefficients are used verbatim;
the species densities come from EQ003 and are therefore disclosed as the only
reconstructed input to the dashed curves.

## EQ009 -- phonon contribution

The source fixes `T_BG approximately 10 K`, a low-temperature suppressed
regime, and a high-temperature linear law, but delegates the relaxation-time
calibration to two external references.  T005 implements a smooth
Bloch--Grueneisen interpolation with its coefficient exposed in configuration.
It is a proxy and is never used to validate the many-body collision kernel.
