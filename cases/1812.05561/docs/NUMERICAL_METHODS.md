# Numerical Methods

| Target | Paper-scale method | Scale/config | Convergence and physics acceptance |
| --- | --- | --- | --- |
| T001 | streamed sparse Krylov; half-chain SVD; checkpointed Nelder-Mead | dynamics N=32; optimization N=20,R=10 | Hermiticity, local first-revival infidelity, ansatz correlation, complete time/entropy grid |
| T002 | translation/inversion sparse projection; full real dense LAPACK | even N=12..32; k=0/even and k=pi/odd | memory preflight, complete sector spectra, GOE proximity, scar overlap isolation |
| T003 | layer-streaming FSA and explicit H-z action | N=32, k=0..32 | beta RMS and H-z spacing relative standard deviation |
| T004 | compact Pauli-string MPO; two-site DMRG; projector-penalized first excitation | open N=60,R=1..8; cutoff 1e-16 | sweep convergence, local residual, discarded weight, ground/first overlap, R=8 gap error |
| T005 | four independent Nelder-Mead lanes and generated cross-cost matrix | N=20,R=10 is a documented section-continuity inference | optimizer convergence, ansatz correlation, own-cost minima |
| T006 | sequential sparse Krylov with three-level local-peak search | N=22..32,m=1..1000; fits 5..60/200..1000 | peak-time resolution, early Gamma collapse, finite increasing turning points |
| T007 | full N=30 k=0/even eigensystems; chunked Schmidt entropy | PXP, h2=0.02, full ansatz | complete clouds, overlap-isolation gain, scar/bulk entropy separation |
| T008 | zero-energy shift-invert and Neel-overlap scar selection in k=0/even and k=pi/odd, followed by caption-specified k=0 filtering | even N=12..32 | per-sector eigenpair residuals, momentum audit, and logarithmic-vs-linear fit comparison |
| T009 | sparse Pauli expansion, complex dense eigensolve, chunked entropy | N=14, Omega=1, three disclosed Gaussian seeds | Hermiticity, integer-period fidelity, exactly N+1 supported states for every seed |

## Paper-review attribution protocol

Every failed paper-scale assertion records the same ordered review categories:

1. implementation/contract defect;
2. numerical convergence, resolution or finite-size effect;
3. missing/ambiguous paper input;
4. potential source/claim discrepancy.

Category 4 is never selected automatically.  It requires explicit exclusion of
1-3 and fresh independent scientific review.  T005 begins with a qualified
input inference; T009 begins with a proven missing random seed and therefore
uses ensemble-invariant rather than pointwise acceptance.
