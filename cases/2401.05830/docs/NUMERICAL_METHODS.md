# Numerical Methods

- Language/runtime: Python with NumPy, SciPy, and Matplotlib.
- Main state space: affine two-dimensional Bloch vector `(y,z)`.
- Independent state space: column-vectorized 2x2 density matrix and a 4x4
  Liouvillian assembled from operator identities.
- Steady states: closed rational form plus independent linear solve.
- Dynamics: exact matrix exponential/modal propagation; no ODE time stepping.
- Crossings: dense bracket plus `scipy.optimize.brentq`.
- Maximal advantage: bounded scalar minimization of `d_cold-d_hot` after the
  crossing.
- Data contract: each target writes CSV before rendering; a manifest freezes
  every CSV SHA-256.
- Reproducibility: no randomness, no author code, no author arrays, and no
  source pixels in numerical generation.

## Method Cards

### NUM001

- Target:
- Equations/method cards:
- Parameters:
- Grid or benchmark:
- Boundary conditions:
- Solver:
- Tolerance:
- Random seed:
- Output schema:
- Validation checks:
- Numerical risks:

## Efficiency And Reuse Plan

- Baseline implementation:
- Main bottleneck:
- Efficient implementation choice:
- Complexity or scaling:
- Performance bottleneck removed:
- Optional harness promotion candidate:
- Case-specific parts that should not enter the harness:
- Performance evidence:
