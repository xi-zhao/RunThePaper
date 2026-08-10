# Method Trace

| Method | Paper source | Independent implementation | Verification |
|---|---|---|---|
| Gaussian Slater state | Numerical implementation appendix | `neel_orbitals`, `correlation_matrix` | particle number and orthonormality tests |
| Uniform hopping | Hamiltonian in main text | `apply_uniform_hopping` | dense `expm` equality to 2e-13 |
| QSD/QSDc Trotter step | numerical appendix after Eq. (6) | `qsd_step`, `evolve_qsd` | invariants + phase-transition probe |
| QJ event evolution | supplement Eq. (3), steps (i)–(iv) | `evolve_quantum_jumps` | covariance update equality to 5e-13 |
| Entropy | supplement Eq. (6) | `subsystem_entropy` | product-state zero test |
| Mutual information | main text, Mutual information | `mutual_information` | product-state zero test |
| Equal-time C | main Eq. (7) | `spatial_correlations` | Wick identity test |
| Unequal-time C | supplement autocorrelation section | `two_time_on_site_correlation` | tau=0 covariance identity |
| Random hopping | supplement Eq. (A1) | `evolve_random_hopping_qsd` | Hermitian propagator construction |

No author numerical code was opened or used. The arXiv archive contains only
TeX, bibliography, and source-figure PDFs.
