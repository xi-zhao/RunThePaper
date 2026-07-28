# Performance Profile

## Goal

- Paper: *Programmable Open Quantum Systems*
- Paper ID: `2512.08279`
- Correct baseline: direct CVXPY formulation of the paper's fixed-retrieval
  SDP.
- Performance target: complete all 82 paper-grid optimizations locally while
  proving feasibility on all 1000 source times.
- Performance is required for paper-scale reproduction because a reduced time
  grid alone would not establish that one retrieval map programs the full
  disclosed family.

## Hardware

- Apple M4, 10 reported CPU cores
- 16 GiB unified memory
- Python 3.12.13
- CVXPY 1.9.2, SCS 3.2.11

## Measured Runs

| Target | Method | Runtime | Peak memory | Result |
| --- | --- | ---: | ---: | --- |
| Main Fig. 2 | one \(32\times32\) signed-channel decomposition plus sampling | 0.126 s | negligible | passed |
| Main Fig. 3 profile | 101 active times, selected epsilon values, full-grid certification | 77 s | about 540 MiB | passed |
| Main Fig. 3 final | 82 warm-started SDPs; 101 active times; all 1000 times certified | 1018.27 s | 744,226,816 bytes | passed |

## Efficient Implementation

The direct 1000-constraint formulation repeats many small diamond-norm
certificates and makes canonicalization expensive. The final implementation
uses a deterministic 101-point active subset:

1. optimizing the subset gives a lower bound on the full-grid optimum;
2. the recovered retrieval map is evaluated at each of the remaining 899
   times;
3. \(Z=|J(\Delta_t)|\) gives an inexpensive feasible diamond-norm upper bound;
4. only inconclusive times use a batched exact Watrous SDP;
5. if every omitted time passes, the same candidate is full-grid feasible,
   making its objective a matching upper bound within solver tolerance.

This is a proof-producing reduction, not a coarse-grid approximation.

## Optimization Boundary

| Code | Scope | Reason |
| --- | --- | --- |
| Choi reshuffling, partial traces, HP diamond SDP | reusable candidate | general quantum-channel operations |
| active-set/full-grid certificate pattern | reusable workflow candidate | separates optimization scale from verification scale |
| SWAP/Bell processor and \(H=0/Z\) models | case-local | paper-specific physics |
| plot style and source grids | case-local | paper-specific evidence contract |

## Acceptance

All correctness checks passed before performance was credited. No scientific
target was reduced or deferred.
