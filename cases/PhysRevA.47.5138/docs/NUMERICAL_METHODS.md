# Numerical Methods

## NUM001 — Figs. 2 and 3

- Equations: EQ001, EQ002, EQ004.
- Scale: S=20, Hilbert dimension 41.
- Grid: declared theta/phi mesh; Q is stored before rendering.
- Solver: exact diagonal phase for OAT; Hermitian spectral evolution for TACT.
- Randomness: none.
- Output: one long-form CSV containing panel ID, angles, Q and normalized Q.
- Risks: phase convention, sphere projection and aliasing near split lobes.
- Checks: state norm and printed Qmax landmarks.

## NUM002 — Fig. 4

- Equations: EQ003, EQ004, EQ005, EQ006.
- Scale: declared physical S values through S=100.
- Solver: bounded scalar minimization; TACT eigensystem reused for all trial mu.
- Randomness: none.
- Output: CSV with exact and asymptotic variances and minimizing times.
- Risks: false later minima, scalar-boundary clipping and finite-S asymptotics.
- Checks: independent direct-state OAT covariance, CSS limit, tolerance doubling,
  positivity and approach to the two printed asymptotes.

## Efficiency Boundary

The largest matrix is 201x201. Local CPU is sufficient; A100 scheduling would
cost more setup time than computation. Dense Hermitian eigensystems are kept
case-local because operator normalization is paper-specific.
