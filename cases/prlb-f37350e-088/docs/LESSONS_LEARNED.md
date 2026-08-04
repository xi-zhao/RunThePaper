# Lessons learned

## New Failure Modes

- A covariance closure can already contain a coefficient that is accidentally multiplied only once in the graded variance.
- A boundary-layer width does not by itself determine the optimizer shift; stationarity can select a smaller scale with a unique limit.
- Finite rings retain discrete-momentum parity even when the thermodynamic Bloch formula looks N independent.
- Cesàro cancellation of generators does not imply exact cancellation of noncommuting exponential products.

## Reusable Checks Or Tools

- Propagate every supplied closure algebraically before numerical optimization.
- Derive the scaled stationarity equation and then verify several extreme nuisance parameters.
- Test exact homogenization claims first on `N=4` and `N=6`; the contrast reveals hidden momentum-grid dependence.
- For Floquet products, check commutators before replacing ordered exponentials by the exponential of an average.

`copied_to_backlog`: add covariance multiplicity and finite-ring momentum-grid gates.
