# Scientific Derivation

## Interacting bath

Partition the one-body density matrix into impurity and environment blocks.
The retained left singular vectors of the environment-impurity block define
the density-matrix bath:

$$
\gamma_{EI}=U_\gamma s_\gamma V_\gamma^\dagger,
\qquad B_{\rm DM}=U_\gamma[:,s_\gamma>\varepsilon_\gamma].
$$

At each independently declared real frequency, apply the same construction to
the imaginary environment-impurity Green-function block and orthogonalize the
union against the impurity and density bath:

$$
\operatorname{Im}g_{EI}(\omega_n)=U_n s_n V_n^\dagger,
\qquad B_{\rm GF}=\operatorname{orth}\!\left(\bigcup_n U_n\right).
$$

Diagonalizing the correlated environment density gives the natural-orbital
bath. Only fractionally occupied orbitals satisfying the frozen selection
rule are retained:

$$
D_{\rm env}^{(2)}U_{
m NO}=U_{
m NO}n,
\qquad B_{\rm NO}=U_{
m NO}[:,n\in\mathcal W].
$$

The complete embedding rotation is
$R=\operatorname{orth}(I\cup B_{\rm DM}\cup B_{\rm GF}\cup B_{\rm NO})$.

## Embedded Hamiltonian

After rotating the Fock matrix, density, and two-electron integrals with
$R$, remove the embedded Hartree-Fock contraction exactly once:

$$
\widetilde F_{ij}=F^{\rm emb}_{ij}
-\sum_{kl}\gamma^{\rm emb}_{kl}
\left[(ij|lk)-\frac12(ik|lj)\right].
$$

The interacting embedded Hamiltonian is then

$$
H_{\rm emb}=\sum_{ij}\widetilde F_{ij}a_i^\dagger a_j
+\frac12\sum_{ijkl}(ij|kl)a_i^\dagger a_k^\dagger a_l a_j.
$$

The exact small-system validation reconstructs $F^{\rm emb}$ from these two
terms to machine precision.

## Correlated self-energy and full-space assembly

The independent validation obtains the retarded Green function from the
Lehmann representation in the $N$ and $N\pm1$ sectors and evaluates

$$
\Sigma_{\rm emb}(\omega)=G_{0,\rm emb}^{-1}(\omega)
-G_{\rm emb}^{-1}(\omega).
$$

Each impurity-centred self-energy is rotated back and combined with explicit
democratic weights $w_J$:

$$
\Sigma_{\rm ibDET}(\omega)=
\sum_J w_J R_J\Sigma_{{\rm emb},J}(\omega)R_J^\dagger.
$$

The paper's GW replacement is implemented with the printed sign structure:

$$
\Sigma_{\rm GW+ibDET}
=\Sigma_{\rm GW,full}+\Sigma_{\rm CC,ibDET}-\Sigma_{\rm GW,ibDET}.
$$

When the embedded CC and GW self-energies coincide, this reduces exactly to
the full-system GW result.

## Spectral observables and nonlocal counterfactual

For overlap matrix $S(\mathbf k)$, the retarded lattice Green function and
spectral weight are

$$
G(\mathbf k,\omega)=
\left[(\omega+\mu+i\eta)S(\mathbf k)-F(\mathbf k)
-\Sigma_c(\mathbf k,\omega)\right]^{-1},
$$

$$
A(\mathbf k,\omega)=-\frac1\pi
\operatorname{Im}\operatorname{Tr}[S(\mathbf k)G(\mathbf k,\omega)].
$$

For the sodium locality test, define the beyond-GW correction in real space
and retain only its same-cell block:

$$
\Delta\Sigma(\mathbf R,\omega)=
\Sigma_{\rm CC}(\mathbf R,\omega)-\Sigma_{\rm GW}(\mathbf R,\omega),
\qquad
\Delta\Sigma_{\rm local}(\mathbf R,\omega)=
\delta_{\mathbf R,0}\Delta\Sigma(\mathbf R,\omega).
$$

The difference between the full and local-only spectra isolates the nonlocal
correlation contribution. A discrete Fourier round trip independently checks
the neighbour-shell representation.

## Evidence boundary

Every formula is bound to `EQUATION_CARDS.json`, source pinpoints, independent
code, and focused tests. No source pixels, author code, or author numerical
arrays enter these equations. The missing production EOM-CCSD/GW campaign and
unpublished parameter choices still prevent paper-exact target claims.
