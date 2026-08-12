# Method Trace

## NUM001 - closed-form steady-state and spectral sweeps

Evaluate the derived rational steady state, characteristic roots, Supplemental
Eq. (11) coefficient, and bifurcation condition directly on immutable grids.
Cross-check steady states with an affine solve and spectra with
`numpy.linalg.eigvals`.

## NUM002 - exact quench propagation

Subtract the final fixed point, diagonalize the real 2x2 homogeneous Bloch
matrix, and evaluate the exact modal exponential for every time.  This avoids
time-step error.  A separately assembled 4x4 density-matrix Liouvillian is
propagated with `scipy.linalg.expm` at audit anchors.

## NUM003 - crossing and maximum-advantage sweep

Bracket the first nontrivial sign change of `d_cold-d_hot`, refine it with
Brent's method, then minimize the signed difference on the post-crossing
interval.  Check every reported root explicitly and compare the optimizer with
the dense grid used for bracketing.

## REVIEW001 - literal-main falsification comparator

Build a second Liouvillian using Main Eqs. (1)-(2) exactly as printed.  Never
use it to generate a reproduction curve.  Verify that its steady state at
`gamma'` equals the figure-consistent steady state at `gamma'/2`, quantifying
the paper's internal rate-normalization discrepancy.

Use this file for algorithmic or systems papers where the key reproduction
object is a method rather than a formula.

## Method Cards

### METHOD001

- Source:
- Role:
- Inputs:
- Outputs:
- Algorithm steps:
- Parameters:
- Code pointer:
- Checks:
- Status:
- Open questions:
