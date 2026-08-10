# Numerical Methods

The simulation stores an `n x 2n` `uint8` stabilizer generator matrix. Random two-qubit Clifford actions update four columns over GF(2); Z measurements use one anticommuting pivot row. Pure-state entropies require ranks of only the reference columns. T003 uses a variable-rank mixed stabilizer group: recorded measurements condition the state, while unrecorded outcomes apply an exact dephasing channel. Its wide complement rank uses packed Python bit vectors with parity tests against the transparent dense elimination.

The independent random seed is `19100020`. Each target gets a separate child stream. The paper does not report its seeds or trajectory counts, so the values in `config/reduced_scale.json` are reproducibility choices, not recovered author metadata.

| Target family | Reduced sizes / samples |
| --- | --- |
| transition | L=8,16,24,32; 96 trajectories per `(L,p)` |
| main light cone | L=48; 480 trajectories |
| incomplete-record conditioning | L=48; 144 trajectories per `(p,cutoff)` |
| surface order | L=12,20,28,36; 112 trajectories |
| correlation collapses | L=8,12,16,24; 72 trajectories per branch |
| supplemental light cones | L=40; 320 trajectories per initial condition |
| supplemental purification | L=8..32; 96 trajectories per `(L,n_ref)` |

The reusable paper-scale campaign in `config/paper_scale.json` covers every printed size through L=512, uses deterministic non-overlapping trajectory identities, atomic checkpoints, 62,976 resumable shards, 16-worker CPU execution, frozen aggregate hashes, and an explicit scientific claim assessor. The final paper-scale campaign has not been run. A100 is not used because these branch-heavy GF(2) tableau updates do not map efficiently to dense GPU kernels; the institute high-CPU profile is the honest route.
