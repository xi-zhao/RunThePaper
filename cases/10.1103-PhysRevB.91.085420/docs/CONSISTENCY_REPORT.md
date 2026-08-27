# Consistency Report — PRB 91, 085420 (2015)

Internal (non-figure) checks that gate the physics:

| Check | Result |
| --- | --- |
| Floquet operator unitarity | U^dag U = I to 1e-14 |
| Undriven limit K=0 vs analytic hopping bands | match to 1e-4 |
| Initial populations sum_n rho_{n,k}(0) | = 1 to 1e-10 |
| k-reflection symmetry rho_{n,-k}, omega_{n,-k} | equal to 1e-6 (Eq. 10 assumption) |
| Fukui Chern numbers | exact integers, sum = 0 |
| Chern transition location | jump at J=K in (5.14, 5.18], matches paper ~5.14 |
| Chern magnitudes | (4,8,4) below, (8,16,8) above (paper (4,-8,4)->(-8,16,-8) up to sign) |
| Fast (Strang) vs exact (eigh) evolution | agree to O(dt^2), 3e-3 at n_sub=320 |
| <x>(t=0) | = 0 to 1e-9 |
| sum_n Delta rho_{n,k} (conservation) | = 0 to 1e-9 (actual and theory) |
| Theory total Delta<x> vs exact dynamics (J=K=4) | 3.08 vs 3.10-3.15 (~2%) |
| Delta<x> T-independence (six T at J=K=4) | mean 3.117, std 0.021 |

Cross-figure consistency: Fig. 3 (theory total 3.08, Berry-only 4.33) and Fig. 4
(theory 4.3x closer to actual than Berry-only) both demonstrate the same
conclusion — the Berry-curvature integral alone is wrong, the IBC correction is
required. The complete case suite passes 15/15 tests: nine model checks, two
reduced-campaign checks, and four frozen paper-scale contract/attestation checks.
The successful paper-scale attestation records 0 denied accesses and 0 forbidden
access attempts.
