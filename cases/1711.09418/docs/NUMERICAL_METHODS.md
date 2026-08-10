# Numerical Methods

## NUM001 — charge-resolved thermodynamics

- Target: T001, Main Fig. 2.
- Solver: `scipy.linalg.eigh` on the central 96 eigenvalues of a dense real symmetric Toeplitz matrix.
- Size: paper-exact `L=10000`; no reduced lattice.
- Recurrence: exact Poisson-binomial charge convolution with entropy-weight propagation.
- Tolerance: probability normalization `1e-12`; entropy sum `1e-11`; particle-hole residual `5e-11`.
- Output: 11 charge rows plus the 96-mode diagnostic spectrum.
- Numerical risk: insufficient active window. Controlled by requiring the window edges below `1e-13` and above `1-1e-13`.

## NUM002 — integrated spectrum

- Target: T002, Main Fig. 3.
- Enumeration: all `16,777,216` occupations of the 24 closest-to-zero modes.
- Sectors: all, and `Delta N_A=0,1,2,3,4,5`.
- Display range: ranks `1...1000`, horizontal coordinate `0...10`.
- Analytic solver: 512-point Gauss-Legendre quadrature at 501 horizontal coordinates.
- Random seed: not applicable; the calculation is deterministic.
- Numerical risk: branch mislabeling. Controlled by the sector-onset physics test and explicit series semantics.

## Paper-scale resumable lane

- Entrypoint: `scripts/run_paper_scale.py --config config/paper_scale.json`.
- Shared preparation: the 96-mode correlation eigenspectrum is computed once
  and atomically checkpointed.
- T001 resume unit: every eight completed correlation modes. A checkpoint
  stores the next mode plus the exact probability and entropy recurrence state.
- T002 numerical shards: 16 canonical contiguous ranges of the `2^24` integer
  occupation labels. Each chunk contains at most 131,072 transient states and
  retains only the top 1,000 log weights for `all,0,...,5`.
- T002 analytic shards: four canonical portions of the 501-point x grid.
- Aggregation rejects missing, overlapping, wrong-config, wrong-eigenspectrum,
  or noncanonical shards, then takes the exact global top-k union.
- Resume safety: checkpoints bind the effective config (including
  implementation version) and, where relevant, the correlation-array hash.
- Backend parity: SciPy partial eigensolve vs independent NumPy full eigensolve;
  streaming top-k vs the original monolithic enumeration on a 12-mode smoke
  case.
- No source PDF, figure, digitized curve, author code, or author numerical array
  is a runner input.

## Efficiency And Reuse

- A Toeplitz first column avoids materializing an integer-difference matrix before the required dense matrix.
- Partial symmetric eigensolving avoids computing 10,000 unused eigenvalues.
- Charge recurrence is `O(m^2)` in the 96 active modes, rather than a sampled Fourier transform.
- The historical 24-mode vectorized run finished in 108.003 s locally. The new
  exact streaming lane trades modest extra merge overhead for bounded memory,
  independent shards, and interruption recovery.
- The scientific methods remain case-local; the isolated runner and hash-guarded RenderContract are generic harness mechanisms.

## Review classification

The numerical runner reports observables and acceptance only. It emits
`paper_error_candidate=false`. The Fig. 3 label discrepancy remains
`inconclusive` until protocol-v2 requirements—paper-exact evidence,
convergence, two independent checks, explicit falsification, quantified
strict-reference discrepancy, and fresh review—are jointly met.
