# Pontus-Mpemba effects: acceleration including preparation time

**The principal physical results are reproduced.** All eight declared numerical panels were computed independently. The three PME classes and the advantage of the two-stage protocol survive inclusion of the auxiliary preparation interval. Seven protocols give speedups of approximately 1.07–2.21 at trace-distance threshold 10⁻³.

The remaining differences have small physical impact. In Fig. 2(c), the distance initially falls from 0.5 to approximately 0.499315, a 0.14% dip at t≈0.0037587. The public notebook's output spacing of approximately 0.01003 skips that feature. Output sampling is distinct from adaptive internal integration steps; the negative initial slope can be derived directly. This local detail does not alter the verified strong PME or total acceleration.

Both literal printed parameters and the declared-steady-state reconstruction are retained. Every reconstructed matrix element changes by at most the two-decimal rounding interval 0.005. A factor-two velocity convention affects the color scale, not trajectories.

[Illustrated report](../docs/report/index.html) · [Derivation](../docs/DERIVATION.md) · [Rerun instructions](../docs/NUMERICAL_METHODS.md)

Independent generation uses Bloch dynamics; distinct checks construct the full GKSL action in a matrix-unit basis. Author notebooks were accessed only after independent generation and were not used to supply generated arrays. The recorded assessments are evidence-bounded numerical findings, not a general formal proof.
