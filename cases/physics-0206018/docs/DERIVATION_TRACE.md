# Derivation Trace

## BEM001 — Helmholtz Green representation

For a piecewise homogeneous two-dimensional dielectric, TM polarization obeys

`(nabla^2 + n_j^2 k^2) psi = 0`.

Using the outgoing Green function

`G_j(r,r';k) = -i H_0^(1)(n_j k |r-r'|)/4`

and subtracting `G times` the wave equation from `psi times` the Green equation,
Green's theorem converts the area problem into

`psi(r') = integral_Gamma [psi partial_nu G - G partial_nu psi] ds`.

The source-normal derivative follows from `dH_0(z)/dz=-H_1(z)`:

`partial_nu G = i n_j k cos(alpha) H_1^(1)(n_j k |r-r'|)/4`.

This identity is evaluated directly from boundary geometry; no field values
are read from the paper figure.

## BEM002 — boundary limit and dielectric matching

Taking the target to a smooth boundary in the Cauchy principal-value sense
contributes one half of the boundary field. With

`B=-2G`, `C=2 partial_nu G-delta`, and `phi=partial_nu psi`,

the homogeneous boundary equation is `B phi + C psi = 0`. Every physical
interface contributes one equation using the interior refractive index and
one using the exterior index. TM continuity identifies the same boundary
`psi` and the same fixed-normal derivative `phi` on both sides. The sign
convention is not accepted by inspection alone: the implementation is checked
against the analytic circular-cavity characteristic equation before the
hexagon result is admitted.

## BEM003 — constant elements and singular diagonal

Each boundary is split into constant elements. Off-diagonal kernels are
integrated with Gauss-Legendre quadrature on the actual line element. For a
smooth element of length `Delta s_l` and curvature `kappa_l`, the small-argument
Hankel expansion gives

`C_ll = -1 + kappa_l Delta s_l/(2 pi)`,

`B_ll = Delta s_l/pi [1-ln(n_j k Delta s_l/4)+i pi/2-gamma_E]`.

Straight polygon sides have zero curvature away from the vertices. The paper
does not specify its exact corner-rounding curve or nonuniform element map;
therefore the first reproducible run uses explicitly declared sharp polygons
and reports this as a fidelity limitation, rather than inferring the rounding
from source pixels.

## BEM004 — scattering spectrum and optical theorem

For an incident plane wave `psi_in=exp(i k_i dot r)` and
`phi_in=i(k_i dot nu)psi_in`, the exterior boundary row becomes the
inhomogeneous equation `M u=M_0 u_in`. The independently generated boundary
solution gives

`f(theta)=(1+i)/(4 sqrt(pi k)) integral exp(-i k_f dot r)`

`times {i(k_f dot nu)(psi-psi_in)+(phi-phi_in)} ds`.

The cross section is evaluated both by angular integration of `|f|^2` and by
the two-dimensional optical theorem

`sigma=2 sqrt(pi/k) Im[(1-i) f(theta=phi)]`.

Agreement of these two routes is a numerical consistency check.

## BEM005 — complex resonance and null field

A resonance is a complex `k` for which `M(k)` is singular. Starting at the
scattering peak, trace-Newton iteration uses

`k_next=k-q/tr[M(k)^(-1) M'(k)]`,

with a finite-difference matrix derivative. The right singular vector
associated with the smallest singular value supplies `(phi,psi)`. The near
field is reconstructed from the boundary integral itself, and the far field
from the same boundary vector and outgoing Hankel asymptotics. Consequently
Fig. 6 and Fig. 7 are downstream views of one frozen numerical solution, not
independently tuned pictures.

## BEM006 — discretization validity

The paper's resolution criterion is

`b=lambda_local/Delta s = 2 pi/(n Re(k) Delta s) >= 4`.

Every run records `b`, matrix dimension, condition/minimum singular value, and
mesh convergence. The publication used `2N=3200` unknowns; a smaller local run
may establish the scientific feature but cannot establish the declared
discretization class. Even the full-scale run remains a figure-defined
publication variant while the prose/Fig. 4 displacement-sign conflict is open.

## Evidence boundary

The supplied EPS/PDF figures are excluded from the runner. They are used only
after output arrays are frozen, to compare axes, peak locations, spatial lobes,
and far-field directionality. Author numerical code and numerical data are not
used.
