# Numerical Methods

## NUM001 — Fig. 2(b) mechanism proxy

- Target: T001.
- Equations/method cards: EQ001, EQ002, METHOD002.
- Parameters: distance 5, loss probability 1% per opportunity, four displayed
  depths 2/4/6/8, 200,000 shots per point, seed 250220558.
- Model: classical repetition-code analogue. A loss randomizes the lost readout
  and can flip a partner bit; SSR flags are either ignored or used to remove
  randomized readouts before majority decoding.
- Output schema: failures, Jeffreys plot rates, mean flagged losses, seed, and
  provenance per depth.
- Validation: delayed-erasure information improves the median logical error and
  matches the perfect-time curve in this timing-marginalized proxy.
- Numerical risk: absolute surface-code values are not represented; output is
  permanently labeled `proxy_model` and `exploratory`.

## NUM002 — Fig. 4(b) printed fit

- Target: T002; equation EQ004.
- Grid: 151 lifecycle values on [1,16].
- Solver: direct floating-point evaluation of `7/lifecycle^(1/3)` percent.
- Validation: strict monotonic decrease and exact endpoints from the formula.
- Risk: finite-size markers are not regenerated.

## NUM003 — Fig. 6(b) algorithm counting

- Target: T003; equation EQ007.
- Parameters: GHZ N=16 and the three Appendix-G fixed subroutines.
- Solver: direct combinatorial expressions.
- Validation: all four average/maximum pairs match the printed rules.

## NUM004 — Figs. 14(c), 16(a) lifecycle counting

- Targets: T004/T005; equation EQ006.
- Parameters: distance 9, displayed SE rounds 2-20; one noiseless boundary
  round is excluded from noisy locations.
- Solver: count entangling-gate endpoints and completed lifecycles.
- Validation: SWAP periods one/two share the all-qubit average; conventional
  data lifecycle grows; conventional measure lifecycle is constant; finite-d
  and large-d limits are 7.2 and 8.
- Risk: SWAP data/measure role-resolved boundary pairing is not reconstructed.

## NUM005 — Table-I analytic rows

- Target: T006; equations EQ006/EQ007.
- Parameters: all seven methods; polynomial overheads evaluated at d=7 only to
  provide a numerical check while preserving the printed symbolic formula.
- Validation: method count, lifecycle constants, and overhead polynomials.
- Risk: threshold/effective-distance rows are circuit simulations and excluded
  from this analytic target.

## Efficiency And Reuse Plan

- Baseline implementation: vectorized NumPy proxy; closed-form analytic targets.
- Main bottleneck: the current clean-room system lacks the paper-scale
  surface-code circuit and correlated-decoder capability; this is recorded as
  an attempted capability limit, not an external-data blocker.
- Complexity: proxy `O(shots * distance * rounds)`; other targets `O(grid)`.
- Case-specific boundary: the repetition-code analogue remains case-local and
  must not enter the general harness as a surface-code substitute.
- Reusable candidate: a generic scientific-input inventory that distinguishes
  vector plot assets from permissible formula/method inputs and independently
  generated numerical data.
