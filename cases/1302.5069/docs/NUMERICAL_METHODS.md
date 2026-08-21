# Numerical Methods

- **Primary solution:** closed Lorentzian survival amplitude, evaluated in a critical-point-safe `sinhc` form.
- **Independent solution:** two-amplitude pseudomode ODE with DOP853 and strict tolerances.
- **Observable:** excited-state population and its analytic derivative; no time-local rate is integrated through strong-coupling poles.
- **Norms:** direct singular values of the `2 x 2` density derivative and analytic factors `1`, `sqrt(2)`, `2`.
- **Sweep:** all paper parameters and the printed `gamma0/omega0` range `0..150`; 1501 coupling points.
- **Integration:** 8193 time points, with a 16385-point convergence campaign.
- **Scientific inputs:** paper formulas and printed parameters only. Author code, author arrays and source pixels are excluded.
