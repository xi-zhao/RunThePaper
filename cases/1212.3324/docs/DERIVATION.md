# Scientific derivation

## Scope and clean-room boundary

The implementation was derived from the manuscript equations, captions and
parameter statements.  The source archive was inspected only to recover the
manuscript text and figure inventory.  It contains no computational source or
numeric arrays.  No plotted pixels or digitized curves enter any Hamiltonian,
grid, observable, assertion or generated data file.

## Piecewise square-lattice drive

For the four hopping steps the Bloch Hamiltonian is

$$
H_n(\mathbf{k})=-J[\cos(\mathbf{k}\cdot\mathbf{b}_n)\sigma_x-
\sin(\mathbf{k}\cdot\mathbf{b}_n)\sigma_y]+\delta\sigma_z,
$$

and the fifth step contains only the sublattice term.  Each interval lasts
$T/5$, so the one-period operator is the ordered product

$$
U(\mathbf{k},T)=e^{-iH_5T/5}\cdots e^{-iH_1T/5}.
$$

The primitive cell vectors are $(1,1)$ and $(1,-1)$.  Therefore
$k_x=(q_1+q_2)/2$, $k_y=(q_1-q_2)/2$.  This coordinate map reverses
orientation, and crossing either primitive reciprocal seam changes the
sublattice Bloch gauge by $\sigma_z$.  Both effects are included in the Chern
and winding calculations. In particular, every central-difference neighbor
that wraps across either $q_1$ or $q_2$ seam is conjugated by $\sigma_z$ before
the derivative is formed. A gauge-periodic analytic matrix field exercises
both boundary stencils in the regression suite; raw array wrapping would mix
different Bloch bases and slow or corrupt finite-grid winding convergence.

At $JT/5=\pi/2$ and $\delta=0$, each active bond transfers a particle exactly
once.  The four transfers close a bulk orbit, hence $U(\mathbf{k},T)=I$, while
an open boundary leaves a chiral translation.  This independently establishes
the bulk identity and the ideal edge branch behind Fig. 2(c).

## Source convention discrepancy for the sublattice offset

The manuscript defines $\delta_{AB}=\epsilon_A-\epsilon_B$, an onsite-energy
difference, but the displayed two-level Hamiltonian writes
$\delta_{AB}\sigma_z$.  With the standard $\sigma_z=\mathrm{diag}(1,-1)$,
the latter has energy difference $2\delta_{AB}$.  For Figs. 3(a-c), the
reconstruction follows the displayed Hamiltonian literally because the captions
explicitly quote $\delta_{AB}=0.5\pi/T$ for those spectra. The phase diagram is
not inferred from the source raster or from a one-dimensional cut: both
interpretations are evaluated on the same two-dimensional $(J,\delta_{AB})$
grid. At every open-gap point the implementation independently calculates
$W_0$, $W_\pi$ and the upper-band Chern number; exact closings and adaptively
identified closing neighborhoods are recorded as such rather than assigned an
integer label. The onsite-difference branch gives gap closings near
$J/\pi=1.21$ and $2.06$; the literal branch gives approximately $1.08$ and
$1.99$.  The visible phase-boundary labels are about $1.3$ and $2.1$.

The literal branch also reproduces the three published strip-spectrum shapes
substantially better under a post-freeze render comparison without changing any
other model parameter.  This strengthens the diagnosis that the plotted spectra
follow the displayed equation. Exact Pauli eigenvalue algebra and both converged
branches exclude a numerical factor-two artifact, so this is a probable
source-level paper-claim discrepancy. It is still not declared a paper error:
protocol-v2 requires a fresh-context reviewer to attempt an independent
falsification first.

## Gap winding and Chern checks

For each quasienergy gap, the physical evolution is closed with the effective
Hamiltonian defined by that gap's logarithm branch cut.  The invariant is

$$
W[U]=\frac{1}{8\pi^2}\int dt\,d^2k\,
\mathrm{Tr}\left(U^{-1}\partial_tU
[U^{-1}\partial_{k_x}U,U^{-1}\partial_{k_y}U]\right).
$$

This full-evolution integral yields the pairs $(W_0,W_\pi)=(0,0)$, $(0,1)$
and $(1,1)$ for the three representative phases.  A separate gauge-aware
Fukui calculation gives upper-band Chern numbers $0,1,0$, verifying
$C=W_\pi-W_0$ with the chosen band convention.

## Weak harmonic drive

The second model uses the printed two-band vector $\mathbf{d}(\mathbf{k})$ and

$$
H(\mathbf{k},t)=\mathbf{d}(\mathbf{k})\cdot\boldsymbol\sigma+
\Delta_0\cos(\omega t)\sigma_z.
$$

Fourier expansion gives the repeated-zone matrix

$$
(H_F)_{m,m'}=(H_0+m\omega)\delta_{m,m'}+
\frac{\Delta_0}{2}\sigma_z(\delta_{m,m'+1}+\delta_{m,m'-1}).
$$

The cylinder spectra are obtained by a direct partial Fourier transform, not
from the paper curves. A second implementation reconstructs the onsite and
nearest-layer blocks through inverse Bloch-Fourier quadrature and matches the
hand-derived matrix to roundoff at independent momenta. A separate midpoint
time-product calculation verifies that the static upper band has unit Chern
magnitude while the driven Floquet band has zero Chern number.
