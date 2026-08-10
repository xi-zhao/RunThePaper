# Method Trace

| Method | Printed definition | Independent implementation | Validation |
| --- | --- | --- | --- |
| MTH_CLIFFORD | each two-site unitary uniformly random Clifford | enumerate/sample all 720 `Sp(4,2)` actions | group order exactly 720 |
| MTH_MEASUREMENT | independent Z measurement at rate p | GF(2) pivot update per event | Bell purification and tableau validity |
| MTH_ENTROPY | reference entropy/mutual information | restricted stabilizer ranks | exact small Bell/product cases |
| MTH_LIGHTCONE | average change due to measurement at `(x,t)` | event-resolved before/after entropy | causal-weight fraction 0.9897 |
| MTH_SCALING | printed finite-size/power-law ansatzes | reduced-size Monte Carlo plus explicit transforms/fits | crossing, monotonicity, decay checks |
| MTH_PARTIAL_RECORD | incomplete record within spatial cutoff | recorded outcomes condition the state; unrecorded outcomes apply exact dephasing in a mixed stabilizer group | Bell-pair channel distinction, packed/dense GF(2) parity, full-record/pure-trajectory equivalence |
| MTH_RENDER | source-aware styling after data freeze | separate renderer and hash check | all eight data hashes unchanged |
