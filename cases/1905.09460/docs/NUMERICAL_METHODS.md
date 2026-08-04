# Numerical methods

## AAH eigensystems

The paper-sized matrices are dense complex arrays (`610x610` for periodic and
`500x500` for open boundaries).  Each `h` value is diagonalized once; the same
eigenvalues/eigenvectors feed spectra, maximum imaginary energy, IPR extrema,
and edge weights.  The plotted scan uses 51 values on `[0,1.5]`; the paper does
not prescribe a sampling count, while all claim-relevant physical parameters
are exact.

Right eigenvectors are normalized columnwise before IPR or edge calculations.
An edge state must place at least 55% of its norm in one fixed 12-site boundary
window.  This single rule reproduces the paper's `h=0` count (0 left, 3 right)
and is not retuned at later phases.

## Winding

Direct products of 610 eigenvalue differences overflow.  The implementation
uses the scaled determinant circle derived in Supplement S.2 and unwraps its
complex phase.  This is numerically stable and evaluates exactly the derived
topological object rather than a digitized step curve.

## Laser

The paper gives the physical coefficients but omits mode truncation, transient
duration, random seed, etalon phase `phi`, and the dimensionless gain-relaxation
setting.  Supplement Eq. (S-31) gives `theta=phi+pi/2`; we adopt the natural
zero-etalon-phase convention `phi=0`, hence `theta=pi/2`.  We use modes
`n=-60,...,60` and solve the stationary neutral-growth eigenmode of the printed
field equation; gain saturation then sets total intensity through `I=g0/g-1`.
Increasing the window from 101 to 121
modes changes the plotted bandwidth by less than the recorded convergence
tolerance.  The bandwidth is the RMS displacement from the central gain mode.

This target is a method reconstruction, not a claim of reproducing an
unreported random transient trajectory.  It does independently reproduce the
localized-to-broad spectrum transition and all four requested spectral
profiles.

## Etalon

Both exact and first-order complex transmission functions are evaluated at
1201 frequencies spanning four free-spectral ranges.  The thickness cancels
after frequency normalization; it is retained in the parameter record because
it fixes the physical FSR quoted by the paper.
