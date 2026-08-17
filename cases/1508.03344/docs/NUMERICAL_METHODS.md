# Numerical methods

## Core representation

Spin configurations are bit strings in the `sigma_z` basis. Global Ising
parity is conserved, so level statistics are evaluated in one declared parity
sector to avoid symmetry mixing. Open chains are the primary reconstruction,
because the pi-drive Hamiltonians explicitly sum bonds from `1` to `L-1`.
Boundary condition and sector are publication-underspecified and remain
configuration fields.

Piecewise-constant Hamiltonians are diagonalized as Hermitian matrices and
exponentiated spectrally. Floquet phases are sorted on the unit circle; the
adjacent-gap ratio includes the wraparound gap and is cross-checked against the
non-wrapping convention. Eigenstate observables use normalized eigenvectors of
the one-period unitary.

## Disorder and observables

Fig. 1 draws `log h` and `log J` from normal distributions of width one and
sets the period from the printed log-normal bandwidth rule. Fig. 2 draws the
printed uniform intervals for `h_i T1` and `J_i T2`. Every shard has a stable,
non-overlapping seed range.

The implemented spectral function is the positive Lehmann weight
`|<alpha|sigma_i^+|beta>|^2`, histogrammed on the quasienergy circle with a
declared kernel. The source's unsquared matrix element is retained as a
falsification branch, not used silently. Correlator micromotion is propagated
through each drive step and checked for the two predicted crossings.

## Scale boundary

The paper prints only a broad `2,000-100,000` sample range. Exact grids,
sample allocation, parity sector, boundary condition, spectral broadening,
site, eigenstate and disorder realization are absent. Therefore both local and
paper-scale configurations are reconstructed parameter subsets. The
paper-scale channel must be executable and resumable even if the full campaign
is not run.
