# Prespecified finite-bath/time convention test

Fixed0911.4270v2, source M350, omega10, cutoff50, Ohmic omega_c15, r4,
T0/1/2, alpha0..1.5, printed dt.0209 and tmax21 are unchanged. The source
does not specify exact positive bath nodes or the finite quadrature. Four
ordinary choices are declared before this generation: right-endpoint/midpoint
positive equally spaced nodes, each with point-value weights J(omega_j)dw or
exact integrals of J over the corresponding bins. Both approximate the stated
continuous density, but they are different explicitly labelled finite baths.

Five fixed steps span the interior of the four-decimal rounding interval,
.020850001.. .020949999; .0209 remains the center. For each, both the original
0:dt:21 convention and adding the exact endpoint21 are saved. There are40
global conventions, not separately fitted choices per temperature or alpha.
Alpha0:.005:1.5 is a source-blind full-range grid. Nothing reads author curves,
uses arbitrary offsets or optimizes a parameter against reference values.

The checker must retain every original vertex and exactly the previous frozen
`graph_uncertainty` bounds, without recomputing larger slope bounds. It reports
all global choices and identifies any compatible one only as an existence
result, never as authenticated author implementation. The former primary
right-node/point-weight/dt.0209 curve and its four failures remain unchanged.
Any promising convention still needs interpolation-resolution checking, not
acceptance from a convenient coarse-grid coincidence. Finer-time/continuum-
bath results are not substitutes for the original finite displayed target.

The first attempt completed all cases but failed an overstrict zero-coupling
1e-12 sanity check: differencing about1000 highly squeezed entropies accumulated
about3e-10 roundoff from 4.44e-16 probability errors. Its failed receipt is
retained. The raw zero-coupling values are not subtracted from any curve. A
precision-aware operation-count/squeezing roundoff budget is recorded for this
internal guard; the original scientific graph bounds are not changed. Future
guard failures retain actual data for diagnosis rather than losing computed
curves before capture.

## Continuous printed-step diagnostic

After the40 fixed choices, a response-blind calculation uses the physical
coupling .7396419437340154 at the existing calibrated source x of the persistent
T0 point. Its config contains no original response ordinate or tolerance.
For vacuum noise, entanglement is a monotone function of eta=|U00|^2. Its
spectral moment supplies |eta''|<=4 sum(w_j(lambda_j-10)^2). Taylor intervals
therefore bound eta at each j*dt over an entire dt cell. Fixed-n intervals are
split at every21/n inside the printed rounding range, so changing the number
of samples is not ignored. Adding exactly21 is tested separately.

Certainly-positive neighboring entropy increments telescope to run endpoints;
ambiguous increments use their upper interval bound. This bounds the whole
positive variation without treating independent time values as unrelated
errors. Width1e-7 and2.5e-8 partitions check resolution. Eigensystem residual,
orthogonality and explicit arithmetic/Duhamel budgets are reported; this is
a finite-precision enclosure, not a directed-rounding formal certificate.
Neither original graph bounds nor source ordinates enter this generation.

If the continuous enclosure shows that rounding could explain the T0 point,
a uniform1001-step grid tests the four previously frozen physical coupling
conditions. Only their alpha values are transferred as explicit input
parameters; response ordinates and tolerances are excluded. The same clock
must satisfy all four old bounds. Any selected common clock is post-observation
nuisance-parameter calibration, not authenticated author data. It must then be
frozen and checked on the dense full-alpha range/all three temperatures,
including the other446 original points. No pointwise clock selection or
changed tolerance is allowed.

The1001-grid comparison yields a common sample run .0208586.. .0208641
without adding21, and .0208590.. .0208637 with it. The frozen rule selects
the middle sampled clock in the longest run: dt=.0208613 for both policies.
This uses the four original outliers only; it is explicitly post-observation
calibration of one nuisance parameter, not blind recovery of author data.

The next actual generation keeps the original right nodes and point weights,
uses3001 couplings for F2, and tests all450 original vertices with unchanged
bounds. It also regenerates F3 at its original printed step.0417 and predicts
F3 using twice the same base clock, .0417226 (which prints as.0417), without
calibrating it to F3 responses. The doubled-clock relation is an additional
diagnostic hypothesis, not a new source completion requirement. Prior source
values were visible in this context, so these checks are not claimed as a
fresh statistical holdout or independent context.
