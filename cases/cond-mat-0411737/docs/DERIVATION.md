# Derivation

## 1. Continuum basis and gaps

Eq. (1) defines a sublattice x valley basis. In that basis the implementation
constructs

$$
H_0=\hbar v_F\left(\sigma_x\tau_z q_x+\sigma_y q_y\right),
\qquad
H_{\mathrm{SO}}=\Delta_{\mathrm{SO}}\sigma_z\tau_z s_z.
$$

The kinetic matrices anticommute with the mass, so at zero Rashba coupling the
full gap is $2\Delta_{\mathrm{SO}}$. Adding Eq. (4) and diagonalizing the
complete 8 by 8 matrix at $q=0$ gives
$2(\Delta_{\mathrm{SO}}-\lambda_R)$. The runner tests four independent ratios
rather than substituting the printed answer:

$$
H_R=\lambda_R\left(\sigma_x\tau_zs_y-\sigma_ys_x\right),
\qquad
E_{\mathrm{gap}}=2\left(\Delta_{\mathrm{SO}}-\lambda_R\right).
$$

## 2. Zigzag-ribbon geometry

The lattice nearest-neighbour distance is the unit length.  A Bloch cell along
the zigzag edge has translation `(sqrt(3),0)` and contains B rows -1..W-2 and A
rows 0..W-1.  This termination gives coordination 2 at both edges and 3 in the
bulk.  Using equal A/B row ranges would instead create a bearded edge.

Nearest neighbours are found geometrically.  Each second-neighbour term is
assigned

$$
\nu_{ij}=\operatorname{sgn}\!\left[(\mathbf d_1\times\mathbf d_2)_z\right].
$$

The matrix element `i t2 nu_ij s_z` is Hermitian because reversing the path
changes both the imaginary conjugation and `nu`.  Low-energy expansion gives
`Delta_so=3 sqrt(3) t2`, hence the full bulk gap `6 sqrt(3) t2`.

The width-32 result differs from this analytic value by 2.44%, and its gap
differs from width 28 by 1.08%.  At `t2=0`, the central zigzag edge branch is
flat to `1.27e-7 t` over the predeclared interior interval.

## 3. Boundary orientations and full-spin Rashba response

For a directed nearest-neighbour bond $\mathbf d_{ij}$, the printed lattice
term is

$$
i\lambda_R\left(s_xd_y-s_yd_x\right).
$$

The bond displacement enters each 2 by 2 spin block, so Rashba coupling is
consumed by the Hamiltonian rather than stored as unused metadata.  The same
geometry builder constructs both zigzag and armchair terminations.  At zero
Rashba coupling, the armchair half gap falls from `1.93e-3 t` at width 20 to
`5.23e-4 t` at width 44, while the largest-width central state retains edge
weight 0.549.  At finite Rashba coupling, the v11 solver samples the spinful
bulk band edges and then follows every baseline-subtracted, edge-localized
in-gap state over the full Brillouin zone.  It uses zigzag widths 48/58/64,
armchair widths 80/104/128 and nested 192-768 point momentum grids.  All 30
orientation/width/subcritical-coupling combinations span the independently
computed bulk midgap and pass the two-grid convergence gate.  The result no
longer assumes that the crossing remains at zero energy or at a TRIM.

The paper says the spin Hall response receives a small Rashba correction, but
does not print the conserved-spin-current operator delegated to its citation.
The implementation therefore computes the full-Brillouin-zone Kubo response
for the conventional symmetrized current `{s_z,v_x}/2` and labels it a proxy.
It changes by 0.252% at `lambda_R/Delta_so=0.05`, while `[H,s_z]` is explicitly
nonzero.  This checks continuity but does not pretend to close the missing
published observable definition.

## 4. Topology, spectral flow and mass symmetry

For each conserved spin, normalized occupied-state links around a 31 by 31
Fukui mesh produce

$$
C_{\uparrow}=-1.0000000000000018,
\qquad
C_{\downarrow}=+1.0000000000000022.
$$

Thus `|C_up-C_down|e/(4pi)=e/(2pi)`.  A separate finite-cylinder construction
tracks 17 levels per helical branch across 101 flux values.  One `h/e` flux
permutes each branch by one level and pumps one unit of spin `hbar`; the chosen
circumference and ramp factors explicitly satisfy the paper's `L>xi` and
adiabatic inequalities.

An exhaustive search of all 64 sublattice-valley-spin Pauli products finds 16
Dirac masses.  Only `sigma_z tau_z s_z` is spin-dependent and simultaneously
even under time reversal, inversion and the horizontal mirror.  A uniform
parallel field directly opens the expected edge Zeeman gap.  Separately, the
bridge `sigma_x tau_x s_x` gives a two-segment, constant-gap interpolation from
the QSH mass to the trivial `sigma_z` mass, but it mixes valleys and has a
nonzero lattice-translation residual.  It therefore proves only generic
broken-T symmetry-class connectivity; it is not attributed to a uniform field.
The paper does not print the alternative terms it says become allowed.  We
therefore also test the minimal primitive-cell candidate built from its lattice
Rashba term, a uniform in-plane Zeeman field and a staggered sublattice mass.
A 48 by 48 grid appears weakly gapped, but continuous optimization over path
coordinate and the full Brillouin zone finds a direct closing of `9.7e-17 t`.
This falsifies that candidate and leaves the paper's bulk mechanism
publication-underspecified; it does not turn the missing mechanism into a
paper-error claim.

## 5. Edge disorder, interactions and transport

The printed constraint

$$
S=s_yS^{\mathsf T}s_y
$$

is solved as a null-space problem. Its
off-diagonal residual is zero and the diagonal entries agree to `1.11e-16`.
Beyond this single-scatterer identity, 32 independently seeded scalar-disorder
profiles of length 512 are propagated in the helical basis.  Because scalar
time-reversal-symmetric disorder commutes with the propagation generator, each
realization has `R=0`, `T=1` and zero Lyapunov exponent.

For Fig. 2, explicit spin-resolved transmission tensors reproduce
`G=2e^2/h`, zero right-contact charge current, and spin current `eV/(4pi)`.

The leading allowed inelastic operator is represented before any exponent is
inserted.  Its time-reversal transform equals its Hermitian conjugate; four
fermion fields contribute dimension 2 and two derivatives contribute dimension
2, so `Delta=4`.  A direct finite-temperature correlator/Kubo-kernel sweep fits
temperature exponent `-5.000000000000001` and coupling exponent
`-1.9999999999999976`.  The competing weak perturbations are also enumerated:
single-particle backscattering is time-reversal forbidden, the local pair term
vanishes by fermion antisymmetry, and the derivative pair term is irrelevant.

## 6. Microscopic estimate, screening and RG

The first-star calculation is no longer a scalar formula substitution.  Three
reciprocal-space corners per valley and both sublattice phases are assembled
into an explicit Hermitian 8 by 8 matrix.  It matches
`(2pi^2/3a^3) sigma_z tau_z s_z` to `8.9e-16`.  Using the declared,
non-paper-exact `a=2.46 angstrom` then gives 2.203 K versus the paper's crude
2.4 K estimate.  The field estimate similarly gives 0.623 mK using the
declared `vF=1e6 m/s`, which the paper does not print.

The one-loop coefficients in Eq. (8) are derived from a matrix-valued Coulomb
Fock shell integral.  Independent finite differences in momentum and mass
produce `0.250000002` and `0.499999984`; a five-shell sweep independently fits
slopes 1/4 and 1/2. These values then, and only then, enter

$$
g(\ell)=\frac{g_0}{1+g_0\ell/4},
\qquad
\Delta(\ell)=\Delta_0\left(1+\frac{g_0\ell}{4}\right)^2.
$$

For screening, v8 evaluates the neutral four-flavor interband Lindhard integral
from spinor overlaps and energy denominators instead of inserting the expected
power law.  The fit gives `Pi(q) ~ -q^0.994673`; the maximum coefficient error
from `1/4` is 0.00510, the angular-grid change is below `4.8e-7`, and doubling
the ultraviolet cutoff changes the normalized coefficient by at most 0.00255.
Only then is the RPA potential constructed, giving power `q^-0.997149`.
Finally, the self-consistent half-gap stopping condition gives a full gap
14.864 K from the printed `g0=0.74`, cutoff 2 eV and bare full gap 2.4 K.
