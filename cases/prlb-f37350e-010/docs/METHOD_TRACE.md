# Method Trace

## MTH_QUARTIC_QUAD

- Role: independent zero-mode moments and propagator.
- Inputs: positive `lambda`, `V`, and `K^2`.
- Method: rescale to `u=(lambda/(4V))^(1/4) phi0`, exploit evenness, and use
  adaptive quadrature with `epsabs=epsrel=1e-12`.
- Outputs: moments, exact `G_L`, and series-error grid.
- Code: `src/stochastic_zero_mode.py`, `scripts/run_analytic_audit.py`.
- Checks: Gamma moments, high-`K^2` asymptotics, finite outputs.
- Status: verified.

## MTH_SYMBOLIC_SERIES

- Role: independent large-N weak-coupling expansion.
- Inputs: source `W(rho)`, `lambda=t^2`, `mbar^2=mu t^2`.
- Method: insert a saddle ansatz, expand, solve the first correction, then
  expand vector/singlet frequencies.
- Code: `scripts/run_analytic_audit.py::derive_large_n_series`.
- Status: verified.

## MTH_SOURCE_TRACE

- Role: map FP coefficients and distinguish `lambda_v` from `lambda_s`.
- Inputs: local primary-source TeX.
- Method: equation-level text comparison plus independent dimensional checks.
- Status: verified.
