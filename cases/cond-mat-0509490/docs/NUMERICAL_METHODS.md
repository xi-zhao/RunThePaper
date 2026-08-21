# Numerical Methods

- Arrays and linear algebra: NumPy.
- Independent dynamics: SciPy `solve_ivp(method="DOP853")`, `rtol=2e-10`, `atol=2e-12`; the generic endpoint-aware kernel derives the physical sign of `dg/dt` and is called separately for `g=8 -> 0` and `g=0 -> 8`.
- Momentum sums: all positive antiperiodic momenta for the declared even chain.
- Product probability: `sum(log1p(-p_k))` to avoid adiabatic underflow.
- Scaling fit: ordinary least squares in log-log coordinates over `10 <= J tau_Q/hbar <= 1000`.
- Rendering: Matplotlib after scientific CSVs and checks are written.

The validation grid is a declared numerical probe of universal equations because the paper contains no plotted point grid.
