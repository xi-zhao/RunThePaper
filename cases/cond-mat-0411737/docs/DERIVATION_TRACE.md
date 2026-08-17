# Derivation Trace

Use this file for formula-heavy papers. Every implemented equation should map
back to a source equation or an explicit derivation step.

## Formula Lane Rule

Every formula used by numerical code must have:

- a card in `EQUATION_CARDS.json`;
- a human-readable derivation in this file;
- a formula gate result in `outputs/checks/formula_verification.json`;
- a code pointer, or a note that it is not used in code.

Do not open a numerical target until its formula dependencies are traceable and
the formula gate is not closed.

## Equation Cards

### EQ001-EQ002 — Continuum gap

The kinetic matrices anticommute with the intrinsic mass matrix. Squaring the
Hamiltonian at zero Rashba coupling gives
`E^2=(hbar v_F q)^2+Delta_so^2`. At `q=0`, diagonalizing the intrinsic plus
Rashba matrices gives the direct gap `2(Delta_so-lambda_R)` and locates the
printed closing boundary.

### EQ003 — Spin response

For conserved `s_z`, each spin block is a Haldane model with Chern number of
opposite sign. Combining their opposite charge Hall currents with
`J_s=(hbar/2e)(J_up-J_down)` yields `sigma_xy^s=e/(2 pi)`.

### EQ004 — Ribbon matrix

Choose a honeycomb strip with zigzag boundaries and one periodic translation
along the edge. Each nearest-neighbour hopping receives its Bloch phase from
the crossed unit-cell translation. For every second-neighbour pair, find the
unique two-bond path `j -> common -> i` and set `nu_ij` from the sign of
`(d1 x d2)_z`. Multiplication by `i t2 s_z` makes the term Hermitian because
`nu_ji=-nu_ij`. Diagonalizing both spin blocks over `k_x` produces the finite
ribbon bands and edge-state weights.

The bulk expansion around `K/K'` gives `Delta_so=3 sqrt(3)t2`, hence the full
gap is `6 sqrt(3)t2`. This analytic value is the primary numerical anchor for
Fig. 1.

### EQ005 — Transport

One Kramers pair gives two perfectly transmitted charge channels, hence
`G=2e^2/h`. Sorting the two spins into opposite contacts gives the adjacent
spin conductance and four-terminal current printed in Fig. 2.

### EQ006-EQ007 — Bare gap estimates

The paper's first-star matrix element and perpendicular-field Pauli term are
evaluated with explicit units. They are order-of-magnitude checks, not fitted
targets.

### EQ008 — RG flow

Integrating `dg/dl=-g^2/4` gives `g(l)=g0/(1+g0 l/4)`. Substitution into
`d ln Delta/dl=g/2` gives the squared logarithmic enhancement. The reported
renormalized gap is then tested by solving the positive self-consistency root
in kelvin and eV conventions.

## Open Source Questions

- Fig. 1 ribbon width and k-grid are not printed.
- The RG paragraph does not make the half-gap/full-gap convention explicit.
- Three internal equation references are inconsistent and are tracked in the
  review protocol rather than silently corrected.
