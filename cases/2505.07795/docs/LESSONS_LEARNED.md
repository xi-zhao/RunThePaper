# Lessons learned

1. In a non-orthonormal operator basis, coefficients summing to one says
   nothing about the trace of the represented density matrix.
2. A normalization subtraction must use the physical trace functional, not a
   convenient coefficient-space average.
3. Small exact permutation groups can provide stronger gold audits than large
   simulations.
4. Global normalizers omitted from both sides of a linear system may cancel
   after final normalization; the decisive defect here is the wrong physical
   projection, not that cosmetic omission alone.

## New Failure Modes

- `coefficient_sum_as_density_trace`: scalar weights sum to one while the
  represented operator does not.
- `normalization_projection_uses_wrong_measure`: a first-order correction is
  projected using coefficient weights instead of operator traces.

## Reusable Checks Or Tools

- `code/src/mspe_permutations.py` provides cycle enumeration,
  permutation traces, exact finite-time Gram solves, and normalization audits.
- The minimal invariant check is inexpensive enough to run before any GPU
  simulation involving replica-permutation moments.
