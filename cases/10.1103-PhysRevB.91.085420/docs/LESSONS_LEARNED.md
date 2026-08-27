# Lessons Learned — PRB 91, 085420 (2015)

## Pitfalls and how they were resolved

1. **Position expectation of a spreading packet.** The wave packet spreads
   ballistically (~2T sites) while its center moves only a few sites, so a
   real-space FFT of <x> = sum_l l|psi|^2 is swamped by wrap-around/cancellation.
   *Fix*: compute <x> in the gauge-free k-space form i.int dk sum_j phi_j* d_k phi_j
   + sum_j j|phi_j|^2 (spectral k-derivative). It gives the mean directly and
   stays well-conditioned even when width >> <x>. Required Nk ~ 2T to resolve
   phi(k); verified by convergence (T=6144 converged at Nk=12288).

2. **Piecewise-constant adiabatic protocol = product of Floquet operators.** The
   paper introduces each beta step at an integer number of driving periods, so the
   whole cycle is the ordered product of T one-period 3x3 operators. Recognising
   this turned a naively expensive time-integration into a minutes-long laptop job
   and is what makes T=1024..6144 and a 61-point J-scan feasible.

3. **Fast propagator via operator splitting.** H = A(k) + c(t) V(beta) with only
   the diagonal V time-dependent. A Strang split precomputes exp(-i A dt) once per
   k (independent of beta and t), so each period is a few cheap batched matvecs.
   ~30x speedup; validated against the exact eigendecomposition propagator.

4. **Rapidly-accumulated dynamical phase in Eq. (8).** The W(1) term carries
   exp(-i(Omega_n-Omega_m)) with Omega ~ 10^2 rad at T=1024. Using the large-T
   integral T*E instead of the exact discrete sum sum_j omega(beta_j) scrambles
   it. *Fix*: accumulate Omega on the exact protocol; and the overall omega-sign
   convention (Phi uses -(Omega_n-Omega_m)) must be fixed against the exact
   dynamics. Even so, Fig. 2 is intrinsically feature-level (correlation ~0.9),
   not pixel.

5. **W(0) via a single diagonalization.** <psi_n|d_beta psi_m> for n!=m is best
   computed as <psi_n|d_beta U|psi_m>/(lam_m-lam_n) (from d_beta of the eigen-
   equation and <psi_n|U=lam_n<psi_n| for unitary U). This avoids any beta-gauge
   fixing; the physical combination C*_n C_m W_{nm} is gauge-invariant.

6. **Topological invariant as a model check.** The Chern numbers came out (2,-4,2)
   at J=K=3 but (4,-8,4)->(-8,16,-8) across J=K~5.14, matching the paper (up to an
   overall orientation sign). The transition location and jump magnitude validated
   the Bloch/gauge conventions before any dynamics was trusted.

## What worked well

- Deriving/gating the physics first (Floquet spectrum, Chern numbers, k-reflection
  symmetry, undriven analytic limit) before writing any figure code caught the
  convention issues cheaply.
- Cross-validating the analytic theory (Eq. 13) against the *exact* dynamics — not
  just against the paper figure — gave an internal, unit-independent correctness
  check (theory total 3.08 vs dynamics 3.10).

## New Failure Modes

- **Real-space `<x>` of a spreading pumped packet is a false artifact.** The center
  displacement (a few sites) is a tiny first moment of a distribution whose width
  grows ~2T sites; real-space wrap-around/cancellation gives non-converging,
  meaningless `<x>`. Diagnose by checking that the reported width grows with the
  box size (a sign the packet is unresolved), and switch to the k-space spectral
  form.
- **Silent phase-convention flip in perturbative population theory.** Eq. (8) uses
  an accumulated dynamical phase whose sign depends on the e^{-i.omega} vs
  e^{+i.omega} eigenphase convention. A wrong sign yields correct *magnitude* but
  scrambled *k-structure* (correlation ~0.3 instead of ~0.9), which looks like a
  modelling bug. Fix the sign against the exact dynamics, not by inspection.

## Reusable Checks Or Tools

- Gauge-free k-space mean-position `<x> = i.int dk sum_j phi_j* d_k phi_j + sum_j j|phi_j|^2`
  for any k-conserving lattice evolution (see `src/observables.py::x_expectation`).
  Candidate to promote once a second pumping/transport case needs it.
- Strang-split fast Floquet evolver for `H = A(k) + c(t)V` (only diagonal part
  time-dependent): precompute exp(-i A dt) once per k (`src/observables.py::evolve_fast`).
- Fukui-Hatsugai-Suzuki plaquette Chern/Berry-flux on a (k, parameter) torus as a
  model-convention gate before trusting any dynamics
  (`src/theory.py::berry_flux_strips`).
