# Numerical methods

The runner is deterministic, CPU-only, and completes in seconds.

1. Closed oscillator and Laughlin formulas are evaluated in float64 on declared
   Cartesian, radial, and angular grids.
2. The confined delta problem uses a bracketing root solve on the physically
   continuous even-parity branch.
3. `M=2` and `M=4` quartic Hamiltonians are assembled from analytic LLL moments
   and diagonalized with symmetric eigensolvers.
4. The driven spectrum uses exact eigendecomposition of a three-state Hermitian
   Hamiltonian for every declared `(B, Omega)` pair.
5. Density evolution uses exact complex amplitudes of the `m=+/-2` basis.
6. CSV/NPZ arrays are written before plotting; figures are pure render products.

No author code, author array, experimental sample, or source-image pixel enters
any of these calculations. The isolated runner will only be granted access to
`src/`, `scripts/run_reproduction.py`, and `config/paper_exact.json`.
