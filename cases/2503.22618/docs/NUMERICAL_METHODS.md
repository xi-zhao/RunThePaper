# Numerical methods

- Runtime: `uv` with NumPy, SciPy, and Matplotlib.
- Randomness: only three deterministic-seed path checks; the rate itself is
  exact and non-Monte-Carlo.
- Finite sizes: (k=100,500,2000,10000,50000,200000).
- Event probability: every accepted binomial count is evaluated in log space.
- Exact rate: Bernoulli relative entropy at the nearest zero-growth boundary.
- Plot provenance: generated from the JSON audit arrays, not digitized paper
  curves.
