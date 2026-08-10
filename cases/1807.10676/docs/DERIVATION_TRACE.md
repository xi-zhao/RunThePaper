# Derivation Trace

## Core chain

The reproduction follows the paper in this order:

1. `EQ001-EQ002`: build the one-valley momentum-space honeycomb and its Dirac/interlayer Hamiltonian.
2. `EQ003`: diagonalize near the neutrality Dirac point to obtain velocity, gaps, high-symmetry levels, and all continuum bands.
3. `EQ004`: parallel-transport occupied subspaces around a reciprocal loop to obtain Wilson eigenphases.
4. `EQ005`: replace the linear Dirac blocks by the paper's quadratic graphene expansion to test particle-hole breaking.
5. `EQ006-EQ007`: implement the printed four- and eight-band lattice Hamiltonians and their Wilson loops.
6. `EQ008-EQ009`: project the lower four two-valley bands, Löwdin-orthonormalize the frame, Fourier transform it into Wannier densities, and evaluate the effective TB4-2V bands.

Every numerical array is produced by this chain. Original figures enter only after the arrays are frozen and hashed.

## EQ001-EQ003 — continuum model and magic angles

The paper divides the MBM Hamiltonian by `v_F k_D`, where `k_D=2|K|sin(theta/2)`. This leaves a dimensionless kinetic term and the single coupling `alpha=w/(v_F k_D)`. The two momentum sublattices are `G` and `q1+G`; three printed `q_j` offsets connect them with the three printed `T^j` matrices.

Numerically, a complete hexagonal set `max(|m|,|n|,|m+n|)<=N` is used. Sparse shift-invert diagonalization extracts only the eigenpairs around zero. `v*/v_F` is the central-band slope around K. The isolation gap is the minimum distance from the central pair to adjacent bands along a high-symmetry path plus a declared coarse Brillouin-zone grid. The six reported zeros are tested directly, and every adaptive cutoff is checked against one additional complete shell.

## EQ004 — Wilson loop

At fixed `k1`, occupied frames are computed along `k2`. Neighbor overlaps are replaced by their polar-unitary factors before multiplication; the final step contains the reciprocal-lattice embedding. The eigenphases of the product are the plotted Wilson bands. The safety window contains extra Ritz vectors before the central occupied subspace is selected, avoiding branch swaps near close levels.

## EQ005 — particle-hole breaking

Nearest- and next-nearest-neighbour graphene dispersions are expanded around each rotated valley to quadratic order. The `t' k^2 sigma_0` term and trigonal-warping terms break the approximate particle-hole relation. For the top row alpha is fixed; for the bottom row theta is fixed and alpha is recomputed from each printed `(t,t')` pair. No band coordinates are read from the paper.

## EQ006-EQ007 — short-range lattice models

The TB4-1V Hamiltonian is assembled from three C3-related nearest vectors and three second-neighbour vectors. The source TeX repeats the label `delta_2`; C3 closure uniquely supplies the third vector. With `t'=-t/3`, `lambda=2t/sqrt(27)`, and `Delta=0.15t`, the computed Gamma levels match the paper's analytic expressions to machine precision. TB8-2V stacks time-reversed valleys and adds `zeta tau_y mu_z sigma_z`; its lower four bands are then used for the Wilson loop.

## EQ008-EQ009 — Wannier projection and effective model

The lower-four-band projector acts on the four paper-defined valley-mixed trial orbitals. The second `2c` site is the symmetry partner of the first, so the conjugated valley coefficients exchange order there. This is the gauge implied by the compact `t_{1,2}` notation and yields the paper's nonsingular interval `15.8 <= det S(k) <= 16`. Applying `S^{-1/2}` and the discrete Fourier transform produces the plotted real-space density. The TB4-2V plot is evaluated directly from the printed `Upsilon` and `Lambda` lattice sums and tuned parameters.

## Formula gate

All nine equation cards have source, symbolic/analytic, numerical, and code pointers. Machine-readable gate output is `outputs/checks/formula_verification.json`.
