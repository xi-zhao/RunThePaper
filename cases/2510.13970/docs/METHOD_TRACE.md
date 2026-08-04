# Method trace

1. Recover the official APS paper and verify the arXiv/DOI identity.
2. Separate source-derived tasks from benchmark-only extensions.
3. Build all Pauli strings on the full `2^6=64` Hilbert space.
4. Project nested commutators onto the five requested operator sums using Hilbert–Schmidt inner products.
5. Compute the exact one-period propagator with a high-order adaptive dense solve.
6. Independently refine an explicit midpoint product with 64, 128, and 256 time slices.
7. Construct the principal logarithm from unitary Schur eigenphases in `(-pi,pi]`.
8. Test the asymptotic scaling at five frequencies and preserve all raw numbers in JSON.

No A100 was used because the largest dense matrix is only `64 x 64`; local execution is faster and avoids remote state risk.
