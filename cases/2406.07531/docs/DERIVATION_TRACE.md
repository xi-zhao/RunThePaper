# Derivation Trace

## Bath construction

For impurity indices I and environment E, split the mean-field one-particle
density matrix into blocks. The left singular vectors of gamma_EI span B_DM.
For a Slater determinant, adding these environment Schmidt vectors to I
reproduces the impurity density exactly.

On a declared real-frequency grid, evaluate

g0(omega) = [(omega + mu + i eta)I - h0] inverse.

The left singular vectors of Im g_EI(omega) form B_GF after projection away
from I and B_DM. A correlated environment 1-RDM is then diagonalized; the most
fractionally occupied natural orbitals form B_NO. The union is rank-revealed
and orthonormalized to form R.

## Embedded Hamiltonian

Transform F, gamma, and the two-electron integrals with R. Equation (2)
subtracts the embedded Hartree-Fock contraction

Sigma_HF,ij = sum_kl gamma_kl [(ij|lk) - one half (ik|lj)].

The numerical round trip Ftilde plus Sigma_HF equals the projected Fock matrix
to 1.4e-17 in the isolated validation.

## Green function and self-energy

The independent exact cross-check diagonalizes the N and N plus or minus 1
particle sectors. Addition and removal transition amplitudes generate the
retarded Lehmann Green function. Dyson inversion gives

Sigma = G0 inverse - G inverse.

In the noninteracting limit the implementation returns a self-energy below
2e-11. The interacting spectrum integrates to 99.56 percent of the exact
spin-orbital sum rule over the finite frequency window.

## Full-space and GW assembly

Each embedded self-energy is rotated as R Sigma_emb R dagger. Overlapping
impurity-centred contributions are combined with explicit nonzero democratic
weights. Equation (4) then replaces the embedded GW contribution:

Sigma_GW+ibDET = Sigma_GW,full + Sigma_CC,ibDET - Sigma_GW,ibDET.

If the two embedded self-energies coincide, this reduces exactly to
full-system GW.

## Observables

Dyson's equation produces A(k,omega). K integration gives DOS; quasiparticle
roots give gaps and occupied bandwidth. For the Na counterfactual, all
interatomic correction blocks are zeroed while same-atom blocks remain
unchanged. A discrete Fourier transform maps the remaining correction between
momentum and neighbour-shell representations.

## Boundary

This derivation is implemented and tested. The missing production EOM-CCSD
Green-function campaign and unpublished parameter choices prevent
paper-exact target claims.
