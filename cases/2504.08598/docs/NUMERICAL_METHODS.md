# Numerical Methods

## NUM001 — Source-bound sparse qudit evolution

- Targets: T001-T003.
- Equations: EQ001-EQ004; methods MTH001-MTH003.
- Parameters: final-paper coordinates, C6 matrices, level-specific Omega and
  Delta maxima, phi=0, 8.4 us, 300 source time samples.
- Basis: lexicographic product of `|g>,|r1>,...,|rk>`.
- Solver: `scipy.sparse.linalg.expm_multiply` on each left-endpoint constant
  interval, matching the paper's printed Trotter product convention.
- Initial condition: `|gg...g>`.
- Observable: paper target-state probability, all-proper-coloring probability,
  and full final basis distribution.
- Tolerances: strict curve gate correlation >=0.98, MAE <=0.04, final error
  <=0.05; feature curve gate correlation >=0.85, MAE/final error <=0.15;
  distribution feature gate sorted TVD <=0.20 and target/proper error <=0.15.
- Random seed: not applicable; evolution is deterministic.
- Validation: norm, physical units, graph decoding, author CSV comparison,
  source-data hash, and explicit mismatch lists.

## NUM002 — Geometry and control handoff

- Target: T001/T002 hardware boundary.
- Output: every atom coordinate in micrometres and per-level Omega/Delta/Phi at
  five schedule knots.
- Geometry rule: Figure I's Table-2 value is interpreted as physical tetrahedron
  edge length; the normalized coordinate symbol is scaled by `1/sqrt(2)`.
- Validation: one atom per vertex; source profile only; unsupported graph/profile
  combinations fail closed.

## NUM003 — Reference comparison

- Author data are read from the frozen CC BY 4.0 ZIP only after generation.
- Curves use point-aligned error and correlation.
- Distributions retain raw-index TVD and sorted TVD because the author CSV does
  not disclose the basis-index convention.
- Paper-target and all-proper-coloring probabilities are separate observables;
  this prevents graph F's dominant symmetry pair from being confused with all
  mathematically valid colorings.

## Efficiency And Reuse Plan

- Largest basis: 4096 states.
- Main bottleneck: repeated sparse exponentials, not memory.
- Efficient choice: precompute diagonal interactions and sparse drive matrices,
  then cache a graph/profile result across curve and distribution comparisons.
- Scaling: local dimension `(k+1)^N`; this implementation is intentionally a
  small-paper-case exact simulator, not a large-N promise.
- Hardware: local CPU is sufficient; an A100 is unnecessary for this case.
- Reusable boundary: graph/profile/control compiler and comparison metrics.
- Case-local boundary: EV20 level tables, graph geometries, and target-state
  conventions.
