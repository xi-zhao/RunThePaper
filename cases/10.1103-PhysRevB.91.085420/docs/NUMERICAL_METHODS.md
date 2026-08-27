# Numerical Methods — PRB 91, 085420 (2015)

## Bloch / Floquet layer (`src/cdhm.py`)
- Per quasimomentum k the CDHM reduces to a 3x3 Bloch Hamiltonian
  H(k,t;beta) = h_hop(k) + K cos(2pi t/tau) V(beta), V diagonal.
- One-period Floquet operator U(k,beta) = time-ordered product of midpoint
  propagators exp(-i H(t_mid) dt), n_sub substeps per period, batched over k via
  Hermitian eigendecomposition. Unitary to 1e-14; eigenphases converge by
  n_sub ~ 80-120.

## Wave-packet dynamics (`src/observables.py`)
- The adiabatic cycle holds beta fixed per driving period, so it is the ordered
  product of T operators U(k,beta_j), beta_j = 2pi(j+0.5)/T.
- `evolve_fast`: Strang split with exp(-i h_hop dt) precomputed once per k
  (beta/t-independent) and the diagonal potential applied as an elementwise
  phase. ~30x faster than rebuilding U each period; validated against the exact
  eigendecomposition propagator.
- `x_expectation`: gauge-free k-space mean position
  <x> = i.int dk sum_j phi_j* d_k phi_j + sum_j j|phi_j|^2 (spectral k-derivative
  by FFT). Equals sum_l l|<l|Psi>|^2 exactly and stays well-conditioned when the
  packet width (~2T sites) far exceeds the center displacement. Converged at
  Nk ~ 2T (verified: T=6144 stable for Nk >= 12288).

## Analytic theory (`src/theory.py`)
- Berry curvature / dgamma_dk: Fukui-Hatsugai-Suzuki plaquettes on the (k,beta)
  torus; Chern numbers come out as exact integers summing to zero.
- W(0) kernel: <psi_n|d_beta U|psi_m>/(lam_m-lam_n) then /(1-e^{i(w_n-w_m)}), from
  a single diagonalization (no beta-gauge fixing). The physical combination
  C*_n C_m W_{nm} is gauge-invariant.
- Average quasienergy E_{n,k} = (1/2pi) int omega dbeta; dE/dk by central
  difference.
- Delta<x> theory (Eq. 13) = (a/2pi)[ Berry-curvature integral term
  - 2 IBC term ], a = N = 3; overall prefactor fixed by the Thouless limit
  Delta x = a C_n for a filled band and confirmed against the exact dynamics.
- Delta rho theory (Eq. 8) uses the exact discrete accumulated phase
  Omega_n(1) = sum_j omega_n(beta_j); the phase sign is fixed against the dynamics.

## Grids / parameters actually run
See TARGET_LEDGER.md. All paper_exact; n_sub 100-160, Nk 241-12288 depending on
target; 61-point J-scan parallelised over 8 cores.
