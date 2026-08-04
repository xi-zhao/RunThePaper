# Method Trace

## MTH-BINARY-SEARCH

- **Source:** Section 4 and Algorithm 1.
- **Role:** Find the smallest positive integer \(N\) for which the selected
  precision function is at most the paper's target \(\epsilon\).
- **Inputs:** method identity, \(t\), \(\lambda\), \(M\), and \(\epsilon\).
- **Output:** \(N^{min}\) plus the number of precision-function evaluations.
- **Verified precondition:** `EQ-PRECISION-FUNCTIONS` proves that
  \(\hat\epsilon(N)\) is strictly decreasing for \(N>0\).
- **Algorithm:**
  1. Start with `lower=upper=1`.
  2. Double `upper` until
     \(\log\hat\epsilon(upper)\le\log\epsilon\).
  3. Apply a lower-bound binary search on the inclusive integer interval.
  4. Return the first valid integer.
- **Independent checks:**
  - \(\hat\epsilon(N^{min})\le\epsilon\);
  - \(N^{min}=1\) or
    \(\hat\epsilon(N^{min}-1)>\epsilon\);
  - \(N^{min}\) equals the ceiling of the independent Lambert-\(W\)
    continuous threshold.
- **Complexity:** \(O(\log N^{min})\) precision-function evaluations.
- **Code:** `code/src/trotter_bounds.py::minimum_steps`.
- **Status:** `verified`.
- **Open questions:** none.

## MTH-PANEL-RENDER

- **Source:** Figs. 2-3 and their captions.
- **Role:** Render four independently generated series on a logarithmic
  vertical axis for one authorized panel.
- **Inputs:** one target-specific CSV produced by `MTH-BINARY-SEARCH`.
- **Output:** one target-specific PNG; no other target is mutated.
- **Checks:** all four plotted columns exist, the \(M\) grid is ordered, every
  value is positive, and the figure is generated from the same target run.
- **Code:** `code/scripts/run_target.py::render_panel`.
- **Status:** `verified`.
- **Open questions:** exact styling is assessed only after scientific
  generation, in the separate pixel lane.
