# Computational Method Trace

1. Draw one hopping-disorder vector from `Normal(t, delta_t^2)` for each
   `(N, realization)` and reuse it across all compared channel/rate conditions.
   This paired design prevents disorder noise from masquerading as a mechanism
   difference.
2. Build the `N+2` Hamiltonian and rank-one Lindblad jumps.
3. Construct the exact column-vectorized Liouvillian from EQ006 as a sparse
   matrix.
4. Propagate `rho(0)=|1><1|` to a final time or a linearly spaced time grid via
   the action of the matrix exponential.
5. Compute sink efficiency and bright/dark/cavity populations from EQ007.
6. Average observables over the stated realization count; preserve per-sample
   values and standard errors in structured CSV files.
7. For rate optimization, evaluate a declared logarithmic grid and take the
   ensemble-mean maximum. Never maximize each random realization separately.
8. Validate trace, Hermiticity, positivity, dense-versus-sparse propagation,
   one-way sum rule, matched-rate endpoints, and the exponential dark decay
   before accepting plots.

The paper uses dense `scipy.linalg.expm`; the case uses sparse
`scipy.sparse.linalg.expm_multiply` on the identical generator. This changes
the linear-algebra representation, not the physical model or observable, and
makes N=64--96 feasible on the local 16 GB M4.
