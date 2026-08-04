# Numerical Methods

## NUM001 - optimal fringes and expectations

- Targets: T001, T002
- Objects: 2x2 complex density matrices and observables.
- Polar decomposition: Hermitian eigendecomposition of `A^dagger A`; scale by
  the largest singular value.
- Grids: uniform `phi` and `theta` meshes declared in `config/paper_exact.json`.
- Checks: trace-one/positivity, polar reconstruction, fringe probability
  bounds, conjugacy of adjoint expectation values.

## NUM002 - noiseless and noisy variances

- Targets: T003, T004
- Noiseless grid: excludes the singular point `p=0.5` and retains both sides.
- Noise: exact Kraus map at `p=0.01`, `theta=0.3*pi`, gamma in the paper range.
- Derivatives: symmetric finite difference in encoded theta with convergence
  comparison; gamma derivative from the generated variance curve.
- Checks: Hermitian curve equals `1/F_H`; intended non-Hermitian curve equals
  `1/F_nH`; literal printed order differs by exactly four; the Kraus map is CPTP.

## Efficiency And Reuse Plan

All operations are analytic or 2x2 linear algebra. A single CPU run is
sub-second to seconds, and GPU/A100 use would be slower after transfer and
environment setup. The reusable object is the explicit observable-order audit;
plot layout and paper-specific missing-input declarations remain case-local.
