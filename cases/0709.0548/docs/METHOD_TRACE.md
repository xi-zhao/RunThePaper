# Method Trace

| Method | Independent implementation | Evidence |
| --- | --- | --- |
| Two-qubit discord | dense projective measurement grid | `formula_checks.csv` |
| DQC1 invariants | dense block matrix and eigenspectrum | `formula_checks.csv` |
| All-stage control/register separability | explicit spectral product-mixture reconstruction | `separability_certificates.csv` |
| Grouped-control partitions | every PPT negativity and realignment witness through five register qubits | `grouped_partition_witnesses.csv` |
| Finite-n discord | pointwise eigenphase minimization, 500 instances × 41 alpha values × 2 generators | `ensemble_discord_long.csv` |
| Generator audit | QR-Haar versus transparent local brickwork circuit and depth sweep | `ensemble_eigenphases.csv`, `circuit_depth_convergence.csv` |
| Root-grid claim | finite-cell phi sweep from N=4 to 4096 | `root_phi_convergence.csv` |
| First symmetric extension | exact solver-independent SDP contract; no result without certificate | `symmetric_extension_contracts.json` |

All randomness is newly generated from frozen seeds. Author matrices, code, and seed are unavailable and unused. The brickwork circuit is an independent convergence probe, never labeled as the author generator.
