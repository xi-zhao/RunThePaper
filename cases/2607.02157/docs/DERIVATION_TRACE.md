# Derivation Trace

Every formula used by numerical code has a card in `EQUATION_CARDS.json`, a
derivation or verification note here, and a machine check in
`scripts/verify_formulas.py` (results in `outputs/checks/formula_check_details.json`).
`DERIVATION.md` is generated from the cards; do not hand-edit it.

## EQC001 — Collisional map

Eq. (19): rho' = (1-P_th) U rho U^dag + P_th rho_eq(s_n). Convex combination of
two CPTP maps, hence CPTP. Because U = exp(-i H dt) and rho_eq = exp(-beta H)/Z
are functions of the *same* instantaneous H, [U, rho_eq] = 0 and
E(rho_eq) = (1-P_th) rho_eq + P_th rho_eq = rho_eq: the instantaneous Gibbs
state is exactly invariant, which is the thermodynamic-consistency property the
paper's SI I derives from the global Davies-Lindblad construction.
Verified numerically (trace, positivity, Gibbs invariance).

## EQC002 — Mackey-Glass drive and preprocessing

The delay equation is integrated directly. The nontrivial numerical mapping is
the preprocessing. For raw samples \(x\), define
\(y=x-\langle x\rangle\) and
\(s=y\sqrt{0.11/\operatorname{Var}(y)}\). It follows algebraically that
\(\langle s\rangle=0\) and \(\operatorname{Var}(s)=0.11\). The generated
ensemble also stays inside \([-1,1]\), so no clipping changes that identity.
The independent check verifies the mean, variance, support, and spectral peak
near \(\omega_s=0.36\).

This resolves an internal inconsistency in the paper rather than hiding it:
literal per-sequence min-max scaling does not reproduce the paper's own stated
mean and variance. We preserve the published ensemble statistics, while
retaining the unpublished initial-history and integration-step choices as
explicit assumptions.

## EQC003/EQC004 — Holevo capacities and the relative-entropy recast (S13)

chi = S(rho_bar) - sum_x P_x S(rho_x). Adding and subtracting
sum_x P_x Tr(rho_x ln rho_bar) and using rho_bar = sum_x P_x rho_x gives
chi = sum_x P_x [Tr(rho_x ln rho_x) - Tr(rho_x ln rho_bar)] = sum_x P_x S(rho_x || rho_bar).
Verified numerically to machine precision. The memory/predictive ensembles share
the same average (S8/S9, probability product rule) — verified in the binning
implementation (both partitions of the same trajectory set average identically).

## EQC005 — Quantum informational dissipation

Both conditional ensembles reconstruct the same unconditional state
\(\bar\rho\). Therefore

\[
\chi^{\mathrm m}-\chi^{\mathrm p}
=
\left[S(\bar\rho)-\sum_m P_m S(\rho_m)\right]
-
\left[S(\bar\rho)-\sum_p P_p S(\rho_p)\right]
=
\sum_p P_p S(\rho_p)-\sum_m P_m S(\rho_m).
\]

The shared entropy cancels exactly. A random paired-ensemble check verifies
the Holevo-difference and conditional-entropy forms to machine precision.

## EQC006/EQC007 — Coherence decomposition (S53-S56)

With C(rho) = S(Delta(rho)) - S(rho) and S(rho) = S(Delta(rho)) - C(rho),
substitute into chi and group: chi = [S(Delta(rho_bar)) - sum P S(Delta(rho_x))]
+ [sum P C(rho_x) - C(rho_bar)] = I + C. Linearity of Delta gives
Delta(rho_bar) = sum P Delta(rho_x). Since memory and predictive ensembles share
rho_bar, the C(rho_bar) baseline cancels in chi_d, leaving
D_q = sum P C(rho_m) - sum P C(rho_p) (S56). Both identities verified numerically;
C >= 0 follows from convexity of relative entropy of coherence (also EQC015).

## EQC008 — Conditional-state form of injection work

Let \(R\) denote the pre-injection reservoir state of a trajectory. The law of
total expectation gives

\[
\mathbb E[\operatorname{Tr}(R H(s))]
=
\sum_s P(s)\operatorname{Tr}\!\left(\mathbb E[R\mid s]H(s)\right).
\]

Applying this identity once to \(s_n\) and once to \(s_{n+1}\), then
subtracting, gives Eq. (S62). The verification constructs random trajectories,
forms their conditional states, and confirms that the conditional-state work
equals the direct trajectory-averaged energy jump.

## EQC009 — Injection-work identity (S62-S64), re-derived independently

W = sum_p P Tr(rho_p H') - sum_m P Tr(rho_m H)  (S62)
beta*Delta_F = beta[energy terms] - [sum_p P S(rho_p) - sum_m P S(rho_m)]  (S63)
The energy terms in beta*W and beta*Delta_F are identical, so
beta*W_irr = beta(W - Delta_F) = sum_p P S(rho_p) - sum_m P S(rho_m)
           = [S(rho_bar) - chi_p] - [S(rho_bar) - chi_m] = chi_m - chi_p = chi_d.
The S(rho_bar) insertions use only that both ensembles share the average state.
Numerically exact (1e-16) on random paired ensembles; in the simulation the
identity is monitored every step (identity_residual_max) as a code invariant —
it holds by construction when energies use the same binned states as entropies.

## EQC010 — Relaxation dissipation and Landauer bound (S67-S71)

W_relax = -Delta_F_relax = beta^-1 sum P [S(rho_p||rho_eq) - S(E(rho_p)||rho_eq)]
using F(rho) = F_eq + beta^-1 S(rho||rho_eq) and E(rho_eq) = rho_eq (EQC001).
Non-negativity is the data-processing inequality for quantum relative entropy
under the CPTP map E. Verified numerically on random states. Summing
beta*W_irr_tot = sum_n (chi_d_n + beta*W_relax_n) >= chi_d_tot gives Eq. (14);
the first law rewrite gives Eq. (15).

## EQC011 — BKM expansion (S10-S12, S38-S41)

Second-order expansion of S(rho_bar + lam*drho || rho_bar): zeroth and first
order vanish (normalization, tracelessness), leaving (lam^2/2) g_BKM. In the
eigenbasis of rho_bar the metric kernel is
integral_0^inf dx / ((p_j+x)(p_k+x)) = ln(p_j/p_k)/(p_j-p_k)  [S39, verified by
quadrature], and with thermal populations ln p_j - ln p_k = -beta(E_j - E_k),
giving the beta(E_k-E_j)/(p_j-p_k) weight of S40. The quadratic approximation is
verified numerically with an O(lambda^3) remainder (relative error shrinks
linearly in lambda). The unrolled history sum (S30-S34) uses the Wilcox identity
and the linearity of the unperturbed map; we adopt S41/S42 as stated and verify
its ingredients (kernel + quadratic form) rather than re-deriving every algebra
step.

## EQC012 — Accumulation factor and resonance peak (S43-S52)

G(Delta E) is the variance of the conditional mean of the g-filtered history
(S44); with the linear-projection estimator (S45-S47) and a Lorentzian model of
the MG spectrum (S50), the resonance value at Delta E = omega_s follows from the
geometric series sum_tau eta^tau = 1/(1-eta), eta = (1-P_th) e^{-gamma_s dt},
1-eta ~= P_th + gamma_s dt, giving G(omega_s) ~= sigma_s^2 / (4 (P_th+gamma_s dt)^2)
~= 2.27 with the paper's constants (paper: ~2.3, consistent with Fig. S1a).
The full co+counter-rotating sum differs from the closed form by ~20%, as
expected from the dropped counter-rotating term (checked numerically).

## EQC013 — Model Hamiltonians

Taken as definitions from the main text. The unpublished boundary condition of
the cluster chain was *resolved empirically to open* by two independent
fingerprints:

1. Duality symmetry: on a periodic chain, conjugation by the CZ-product
   unitary maps X_i -> Z_{i-1} X_i Z_{i+1} while leaving Z_i (hence the ZZ term
   and the drive H1 = sum Z) invariant, so H(alpha) -> H(1-alpha) exactly. Every
   PBC capacity/thermodynamic curve must then be symmetric about alpha = 0.5 —
   our full PBC scan confirmed this to machine precision
   (outputs/data/fig2_cluster_scan_pbc_symmetric.csv), contradicting the
   paper's asymmetric Fig. 2 bottom row. An open chain breaks the duality.
2. Spectral fingerprint: OBC endpoint spectra (width 10.83 at alpha = 0 vs
   7.24 at alpha = 1, with edge zero modes at alpha = 1) match the paper's
   Fig. S1c; PBC gives symmetric widths 10.83/10.83 and no zero modes.

The PBC bulk gap still minimizes at alpha = 0.50, consistent with the stated
transition point.

## EQC014 — Ridge readout and NMSE

For the regularized objective
\(L(w)=\|Xw-\hat y\|_2^2+\eta\|w\|_2^2\), stationarity gives

\[
\nabla_w L=2X^\mathsf{T}(Xw-\hat y)+2\eta w=0,
\qquad
w=(X^\mathsf{T}X+\eta I)^{-1}X^\mathsf{T}\hat y.
\]

Because \(X^\mathsf{T}X+\eta I\) is positive definite for \(\eta>0\), this
stationary point is the unique minimum. The numerical check verifies the
normal-equation residual, local objective increase, and non-negativity of the
stated NMSE. The constant bias feature remains an explicit unpublished
convention; the full \(4^6-1\) Pauli readout and all published training
parameters are otherwise preserved.

## EQC015 — Markovian bound (S57-S61)

For a first-order Markov drive the predictive state is the causal mixture
rho_p = sum_m P(s_n|s_{n+1}) rho_m (S57). C is convex (verified numerically),
so C(rho_p) <= mixture of C(rho_m); multiplying by P(s_{n+1}), summing, and
marginalizing (S59-S61) yields sum_p P C(rho_p) <= sum_m P C(rho_m), i.e.
D_q >= 0. Non-Markovian drives (Mackey-Glass) break the causal-mixture
structure, permitting D_q < 0 — the paper's quantum-advantage window.

## Known deviations / assumptions

- MG preprocessing calibrated to the published statistics (EQC002 card):
  centered, sigma_s^2 = 0.11, support within [-1,1]; the paper's verbal
  min-max description contradicts its own stated mean/variance.
- Map cache: the propagator/Gibbs pair is precomputed on a 401-point s-grid
  (Hamiltonian error <= lambda * ds/2 ~ 2.5e-4); validated against the exact
  per-step eigendecomposition path before production runs.
- Cluster chain boundary condition resolved to open (see EQC013 above); the
  discarded PBC run is kept as duality-symmetry evidence.
