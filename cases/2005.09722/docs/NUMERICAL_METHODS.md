# Numerical Methods

The implementation is independent and follows only the equations and prose in
the paper.

- Uniform hopping is applied by FFT using the exact single-particle dispersion
  `2 cos(k)`, algebraically equivalent to `exp(-ih dt)`.
- QSD/QSDc use the printed first-order Trotter factor with Gaussian variance
  `gamma*dt`; reduced QR enforces `U†U=I`. QR phases are canonicalized so the
  unequal-time product has a deterministic orbital gauge.
- QJ is event-driven with total rate `gamma*N`. An occupied-site jump is
  implemented through an independent occupied-orbital rotation; tests compare
  its covariance exactly with the appendix update formula.
- Random hopping draws every periodic bond independently from `{-1,+1}` and
  refreshes it once per unit time, as stated in Eq. (A1).
- All nonlinear observables are computed per trajectory before averaging.
- The production profile uses `L≤96`, 8–192 trajectories depending on target,
  and deterministic case-owned seeds. No author seeds or arrays are known.
