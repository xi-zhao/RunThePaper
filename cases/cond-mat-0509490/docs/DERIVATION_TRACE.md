# Derivation Trace

## 1. Free-fermion sectors

Jordan-Wigner transformation turns the periodic spin Hamiltonian into two fermion-parity sectors. The ground state remains in the even sector, whose fermions are antiperiodic. Therefore

\[
k_m a=\frac{(2m+1)\pi}{N},\qquad m=0,\ldots,N/2-1.
\]

The `k,-k` Bogoliubov block is a two-level Hamiltonian

\[
h_k(g)=2J[(g-\cos ka)\sigma_z+\sin(ka)\sigma_x],
\]

with eigenenergy `epsilon_k` in EQ001. At `g=1`, `epsilon_k=4J|sin(ka/2)|`, so the small-momentum velocity is `2Ja`.

## 2. Independent dynamics

For the linear sweep `g(t)=-t/tau_Q`, the paper's time-dependent BdG equation is integrated directly. With `g` as the independent coordinate,

\[
\frac{d\psi_k}{dg}=\frac{i\tau_Q}{\hbar}h_k(g)\psi_k.
\]

The run begins at `g=8` in the positive-energy instantaneous mode and ends at `g=0`; projection onto the final negative-energy mode gives `p_k`. This path does not use the LZ formula and is the independent cross-check.

## 3. Landau-Zener probability

The paper's variable change produces `Delta_k^{-1}=4J tau_Q sin^2(ka)`. The standard LZ transition gives

\[
p_k=e^{-2\pi J\tau_Q\sin^2(ka)/\hbar}.
\]

Slow quenches excite only `ka << 1`, yielding the Gaussian `exp[-2 pi J tau_Q (ka)^2/hbar]`.

## 4. Defect-density integral

Each excited `k,-k` pair contributes two quasiparticles and hence two kinks. Replacing the half-integer sum by an integral and extending the narrow Gaussian to the real line gives

\[
n=\frac{1}{2\pi}\sqrt{\frac{\pi}{2\pi J\tau_Q/\hbar}}
=\frac{1}{2\pi\sqrt{2J\tau_Q/\hbar}}.
\]

The exact prefactor is `1/(2 pi sqrt(2))=0.1125395` in `J=hbar=1` units; relative to the earlier order-one KZM estimate, the multiplicative correction is `1/(2 pi)=0.1591549`.

## 5. Finite-size crossover

Independent mode pairs give `P_GS=product(1-p_k)`. On the adiabatic side only `k=pi/(Na)` contributes, so

\[
P_{GS}\simeq1-\exp[-2\pi^3J\tau_Q/(\hbar N^2)].
\]

The coefficient `2 pi^3=62.0126` lies 4.86% above the earlier reported fit `59`; that comparison is compatible with the analytic result but cannot independently re-create the external fit without its original data.

## 6. Reverse sweep

Changing the sweep direction reverses the sign of the LZ time coordinate, not the transition probability. Numerically, the shared sweep kernel derives the sign from `field_end-field_start`; it separately integrates `g=8 -> 0` and `g=0 -> 8`, starts from the positive-energy mode at each physical initial endpoint, and projects onto the negative-energy mode at the final endpoint. Mode probabilities and their finite-chain density sums are compared only after both integrations finish.
