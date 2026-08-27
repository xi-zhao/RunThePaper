# Derivation Trace

This file is the human-readable formula lane. Formula identifiers match
`EQUATION_CARDS.json`; `DERIVATION.md` is generated from those cards.

## EQC001 — matched state-dependent forces

The paper starts from

\[
V=-C_4(d+x_i-x_a)^{-4}.
\]

For `|x_i-x_a| << d`, the first derivative gives

\[
V\simeq -C_4d^{-4}+4C_4d^{-5}(x_i-x_a).
\]

The constant shifts only the Rydberg branch energy. With
`x_j=l_j(a_j+a_j†)` and the atom projector `P_r`, the displacement coupling is
`omega_g=4 C4 l_i/(hbar d^5)`. Matching the ion Magnus coupling to the same
magnitude yields Main Eq. (1). In units of `hbar omega`, the ion/atom force
pairs for `(g down, g up, r down, r up)` are

\[
(q,0),\;(-q,0),\;(2q,-q),\;(0,-q),\qquad q=\omega_g/\omega.
\]

This mapping is the only branch table used by the dynamics code.

## EQC002 — forced harmonic oscillator

For a branch Hamiltonian `H_I(t)=hbar omega f(a† e^{i omega t}+a e^{-i omega t})`,
the Magnus expansion terminates after the commutator term because the
commutator is a scalar. The evolution is a displacement times a scalar phase:

\[
U_f(t)=D[\alpha_f(t)]e^{i\phi_f(t)},\quad
\alpha_f=f(1-e^{i\theta}),\quad
\phi_f=f^2(\theta-\sin\theta),\quad \theta=\omega t.
\]

At `theta=2 pi m`, every displacement vanishes. The sign convention rotates
the plotted loop but does not change its area or any spin observable.

## EQC003 — conditional CZ phase

Both oscillators contribute their squared force to the scalar phase. Using the
EQC001 branch table gives phase weights `(q^2,q^2,5q^2,q^2)`. The two-qubit
phase invariant is

\[
\Phi=\phi_{g\downarrow}+\phi_{r\uparrow}
-\phi_{g\uparrow}-\phi_{r\downarrow}
=-4q^2(\theta-\sin\theta).
\]

After one period this becomes `-8 pi q^2`; choosing
`q=1/(2 sqrt(2))` therefore gives `Phi=-pi`. Local branch phases can be removed
by one-qubit Z rotations, leaving a CZ.

## EQC004 — trace out motion, then compute concurrence

For the equal spin input and motional vacuum, branch `j` carries two coherent
states `alpha_{j,i}` and `alpha_{j,a}`. The reduced spin density matrix is

\[
\rho_{jk}=\frac14 e^{i(\phi_j-\phi_k)}
\exp\left[-\frac12\sum_{m\in\{i,a\}}
|\alpha_{j,m}-\alpha_{k,m}|^2\right].
\]

This formula makes the state Hermitian, positive, and unit trace by
construction. Rotated-basis populations are direct projectors; concurrence is
the Wootters value from the eigenvalues of
`rho (sigma_y tensor sigma_y) rho* (sigma_y tensor sigma_y)`. Closure restores a
pure spin state at integer periods: concurrence is 1 at `T` and 0 at `2T`.

## EQC005 — process-averaged Rydberg decay

Only half the computational basis occupies the Rydberg branch. Survival over
gate time `T` is `exp(-T/tau_r)`, so the process-averaged loss is

\[
\epsilon_{\rm decay}=\frac12[1-e^{-T/\tau_r}].
\]

For `T=5 us`, this gives 2.438% at `tau=100 us`, 1.234% at `200 us`,
and 0.529% at `470 us`, agreeing with the stated rounded values.

## EQC006 — thermal anharmonic feature model

SM Eq. (S14) makes the leading nonlinear correction a Rydberg-conditional
frequency shift. SM Eq. (S15) gives

\[
\delta\omega/\omega=-5\eta q.
\]

The paper's thermal characteristic-function estimate has scale
`x=10 pi eta q nbar`. Because only half the equal superposition is on the
Rydberg branch, and because the QuTiP curve contains a nonzero zero-point
baseline, the feature model used here is

\[
\epsilon_{\rm anh}(\bar n)=\epsilon_0+
\frac12\frac{x^2}{1+x^2},\qquad
x=10\pi\eta q(\bar n+1/2),\qquad
\epsilon_0=3\times10^{-4}(\eta/1.88\times10^{-3})^2.
\]

This is explicitly reconstructed, not the paper's five-order QuTiP solver. It
matches the disclosed checkpoints at `nbar=1,5,10,20` to feature-level accuracy
and preserves the required `eta^2` low-occupation scaling.

## EQC007 — chain-length duration surrogate

The paper supplies three constraints but not the optimized schedule data:
`T=5 us` below `N*=25`, linear growth above it, and about 7% low-l decay error
at `N=100`. Solving EQC005 for the latter gives approximately 15 us. The unique
minimal piecewise-linear surrogate used here is therefore

\[
T_g(N)=5\ {\rm us}\quad(N\le25),\qquad
T_g(N)=5+10(N-25)/75\ {\rm us}\quad(N>25).
\]

The curve is a reconstruction of the disclosed contract, not an exact copy of
the author's optimized duration vector.

## EQC008 — deterministic interconnect timing

At tweezer speed `v=0.5 um/us`, two atom-ion gates and one shuttle give
`t_hybrid=2T+L/v=10+2L us`. The photon reference is the stated 250 Hz link,
`t_photon=4000 us`. A compact QCCD timing fit `t_ion=600+5L us` reproduces the
source panel's short-distance intercept and order-of-magnitude slope; it is
marked reconstructed because the paper supplies no transport equation.

## EQC009 — hybrid memory amortization and source inconsistency

One write and one read cost `2 p_T`, independent of the number of algorithm
operations. Hence the storage error per operation is

\[
p_{\rm hybrid/op}(N_{\rm ops})=2p_T/N_{\rm ops}.
\]

Its derivative is strictly negative. Pure active memories pay a roughly
constant per-operation syndrome-extraction cost. The source Fig. 4(b) instead
shows all three curves rising with `N_ops`; this contradicts both the caption
and the equation above. The reproduction plots the stated business logic and
emits a failing source-consistency assertion rather than imitating the
contradictory raster.

## EQC010 — Fowler qLDPC projection

The supplemental projection uses

\[
p_L(d)=A_{BB}(p_{eff}/p_{th})^{(d+1)/2},
\]

The exponent has a transparent below-threshold interpretation: a distance-\(d\)
code needs at least \((d+1)/2\) independent faults for a leading logical
failure, so the small parameter \(p_{\rm eff}/p_{\rm th}\) enters to that
power. The prefactor \(A_{BB}\), threshold, and extra 66-fold herald factor are
empirical calibrations, not consequences of that counting argument.

An independent substitution audit does **not** close this card. For example,
using the displayed \(A_{BB}=0.1\), \(p_{\rm th}=3.4\times10^{-3}\), and
\(d=12\), the current implementation gives

\[
p_L^{\rm atom}=3.51\times10^{-5},\quad
p_L^{\rm hybrid}/66=9.26\times10^{-13},\quad
p_L^{\rm ion}=1.11\times10^{-11}.
\]

Table S11 instead reports approximately \(1.4\times10^{-5}\),
\(7\times10^{-12}\), and \(5.4\times10^{-12}\). These are order-consistent but
not generated by one common substitution rule. Until the empirical
calibration/rounding convention is recovered, `EQC010` remains `source_only`
and cannot authorize either the Fig. S5 or Fig. 4 projection runs.

## EQC011 — multi-mode toggle closure

For dimensionless mode frequency `nu_m=omega_m/omega_COM` and total scaled time
`tau=omega_COM t`, a piecewise force schedule closes mode `m` when

\[
\sum_j s_j[e^{i\nu_m\tau_{j+1}}-e^{i\nu_m\tau_j}]=0.
\]

The local optimizer parameterizes positive segment durations by a softmax so
the boundaries remain ordered and sum exactly to one period. Normal modes are
computed from the Hessian of the dimensionless Coulomb-plus-harmonic potential.
The source is internally inconsistent: the prose/Fig. S1 use 25 segments for
`N=10`, while Table S4 lists 17. The reproduction uses 25, which is consistent
with the stated `2N+5` rule.

## EQC012 — operating distance and matched Magnus coupling

Combining `omega_g=4 C4 l/(hbar d^5)` with EQC003 gives

\[
d_{CZ}=\left(8\sqrt2 C_4\ell/(\hbar\omega)\right)^{1/5},\quad
\omega_g=\omega/(2\sqrt2).
\]

This fifth-root dependence explains why an order-one C4 calibration error only
weakly moves the distance.

## EQC013 — circular-state error floors

Let the decay, anharmonic, and technical channel fidelities be
\(1-\epsilon_d\), \(1-\epsilon_a\), and \(1-\epsilon_t\). Under the stated
independent-channel approximation,

\[
\begin{aligned}
1-\mathcal F
&=1-(1-\epsilon_d)(1-\epsilon_a)(1-\epsilon_t)\\
&=\epsilon_d+\epsilon_a+\epsilon_t
 -\epsilon_d\epsilon_a-\epsilon_d\epsilon_t-\epsilon_a\epsilon_t
 +\epsilon_d\epsilon_a\epsilon_t.
\end{aligned}
\]

The paper and case retain the first-order term because every channel is small.
For the largest Table S14 row
\((\epsilon_d,\epsilon_a,\epsilon_t)=(0.012,2.4\times10^{-5},10^{-3})\),
the omitted cross terms are about \(1.23\times10^{-5}\), below the table's
display precision. Direct row-wise addition reproduces all five reported
totals.

Thus the budget logic is independently reconstructed from EQC005 and EQC006,
but it is not fully verified: EQC006 remains a feature model, and the
supplement contains mutually inconsistent circular-\(C_4\) ranges and adopted
operating values. `EQC013` may authorize exploratory error-budget calculations
only; it cannot authorize a final circular-state reproduction.
