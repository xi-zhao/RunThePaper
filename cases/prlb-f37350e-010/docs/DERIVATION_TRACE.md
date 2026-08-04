# Derivation Trace

## EQ001: quartic zero-mode moments

- Source: arXiv:1212.3058, zero-mode functional integral; normalization adapted from `lambda/4!` to `lambda/4`.
- Independent step: evaluate the one-dimensional even moments with a Gamma substitution.
- Code: `code/src/stochastic_zero_mode.py::quartic_moment`.
- Status: verified by direct quadrature.

## EQ002: physical nonzero-mode mass

- Source: arXiv:1212.3058 cross interaction and the prompt's changed potential.
- Independent step: use `V''(phi0/sqrt(V))` or expand one real harmonic.
- Complex-pair cross-check: both free and interaction actions double, leaving
  the inverse propagator `K^2+3 lambda phi0^2/V`.
- Code: `physical_mass_squared` and `frozen_mass_squared`.
- Status: verified; frozen convention is internally inconsistent.

## EQ003: propagator expansion

- Derived from: EQ001 and EQ002.
- Independent step: integrate the exact rational kernel, then compare to the
  geometric expansion over a `K^2` grid.
- Code: `exact_propagator`, `propagator_expansion_coefficients`,
  `weak_mass_expansion`.
- Status: verified; deep-IR wording rejected by the measured error trend.

## EQ004-EQ005: large-N saddle and frequencies

- Source: arXiv:1911.00022 large-N section.
- Independent step: SymPy series in `t=sqrt(lambda)` with
  `mbar^2=mu t^2`.
- Code: `code/scripts/run_analytic_audit.py::derive_large_n_series`.
- Status: verified; frozen Task 4 is incomplete and Task 5 has a label typo.

## EQ006: FP coefficients

- Source: arXiv:1911.00022 Eqs. (8.13)-(8.14).
- Independent step: dimensional and numerical evaluation using the closed
  form `psi(3/2)=2-gamma-2 log 2`.
- Code: `code/src/stochastic_zero_mode.py::fp_coefficients`.
- Status: verified.
