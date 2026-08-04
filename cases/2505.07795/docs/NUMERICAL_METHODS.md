# Numerical methods

- Runtime: `uv run --with numpy --with matplotlib python`.
- Exact groups: (S_2) and (S_3); the largest linear system is (6\times6).
- Precision: IEEE float64 is sufficient because the diagnostic scans only to
  (t=13,d=2); all invariant comparisons have wide separation.
- Plot: rendered only after JSON data was written conceptually and generated
  from the same deterministic in-memory arrays.
- Randomness: none.

The source paper's finite-size circuit plots are not simulated in this case;
their raw data and seeds are absent from the source package.
