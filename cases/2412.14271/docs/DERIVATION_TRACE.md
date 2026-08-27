# Derivation Trace

## DPT001-DPT002: model and open dynamics

The collective spin convention is `[Jx,Jy]=2 i Jz`, so the spin length is
`J^2=N(N+1)` and the symmetric spin space has dimension `N+1`. The published
Hamiltonian and jump operators are

`H = omega_c a†a + (omega_a/2) Jz + (lambda/N) Jx(a†²+a²)`,

`L1=sqrt(kappa1)a`, `L2=sqrt(kappa2/N)a²`.

Vectorizing the density operator gives

`vec(rho_dot)=[-i(I⊗H-H^T⊗I)+sum D_L] vec(rho)`.

This fixes the finite-size ED/Liouvillian calculation without using any
published numerical array. Trace preservation follows because every
dissipator has zero trace.

## DPT003-DPT004: one-photon mean field and instability

After `a -> a/sqrt(N)` and `J -> J/N`, factor spin-photon correlations and
define `X=<a²+a†²>`, `Y=<a²-a†²>`, `n=<a†a>`. Setting the six v1-SM equations
to zero and using `Jx²+Jy²+Jz²=1` gives

`lambda_c = sqrt(kappa1²+4 omega_c²)/4`,

`Jx=±lambda_c/lambda`, `Jy=0`,
`Jz=-sqrt(1-lambda_c²/lambda²)`,
`n=-(omega_a/omega_c) Jx²/Jz`.

The normal branch has `n=X=Y=Jx=Jy=0, Jz=-1`. Differentiating the ODE at
each fixed point gives the Bogoliubov matrix. The published formal parameters
`omega_c=1, omega_a=2, kappa1=0.4` imply `lambda_c=sqrt(4.16)/4≈0.50990`,
matching the threshold marker in formal Fig. 2.

## DPT005-DPT006: both-loss cumulant equations

The two-photon dissipator introduces third/fourth moments. Truncating connected
cumulants above second order yields the eight scaled equations printed in the
v1 supplement for `<a>,<a†>,<a²>,<a†²>,<n>,<Jx>,<Jy>,<Jz>`. A real-valued
representation is used numerically; conjugate variables are constrained rather
than solved independently. Fixed points are followed in `lambda` by seeded
root continuation, and stability is determined from a finite-difference
Jacobian of the same ODE. This independent Jacobian also checks the long
printed Bogoliubov matrix for transcription mistakes.

## DPT007: quantum trajectories

For each trajectory, evolve the non-Hermitian Hamiltonian between stochastic
jumps selected from `L1` and `L2`. The density estimate is

`rho_hat=(1/N_T) sum_i |psi_i><psi_i|`,

and the photon density matrix is `Tr_spin(rho_hat)`. Increasing trajectory
count must reduce sampling noise while preserving trace, positivity, and the
even/odd selection rule when `kappa1=0`.

## DPT008: Wigner transform

For the generated photonic density matrix,

`W(alpha)=(2/pi) Tr[D(-alpha) rho_ph D(alpha) (-1)^(a†a)]`.

Equivalent Laguerre-polynomial evaluation is used by QuTiP. Its integral over
phase space is one, the vacuum limit is Gaussian, and `W(alpha)=W(i alpha)`
tests the weak `Z4` symmetry. Source Wigner pixels are comparison-only.

## DPT009: pure two-photon parity sectors

When `kappa1=0`, both `H` and `L2` change photon number by an even amount.
Photon parity commutes with the Liouvillian, so even and odd initial sectors
cannot mix. Two zero Liouvillian eigenvalues and parity-pure stationary Fock
distributions are therefore the numerical signatures tested in T008.

## Publication gap

Formal S3-S4 cannot be derived panel-exactly from the available sources. The
target remains closed; no curve is inferred from the source image or Zenodo
data.
