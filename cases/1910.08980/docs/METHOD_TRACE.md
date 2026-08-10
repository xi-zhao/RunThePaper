# Method Trace

## MTH_ENSEMBLE — Signed random regular ensemble

- Source: Main Fig. 1 caption.
- Inputs: `n in {32,100}`, degree 3, independent `J_uv in {-1,+1}`, 16 instances.
- Implementation: deterministic NetworkX regular-graph sampling followed by an
  independent NumPy coupling draw; graph and coupling seeds are recorded per row.
- Check: every row has degree three, `3n/2` edges, and only signed unit weights.
- Status: verified protocol; original sample identity unavailable.

## MTH_QAOA — Continuous level-1 QAOA optimization

- Source: Appendix A and Appendix C Eq. (C9).
- Inputs: current integer weighted Ising matrix.
- Algorithm: analytic global beta maximum at fixed gamma; 129-point scan over
  one full gamma period; bounded continuous polishing of the six best basins.
- Output: optimal expected energy, beta, gamma, and all active-edge correlations.
- Check: Eq. (C9) matches direct statevector evolution on a four-qubit signed model.
- Status: verified.

## MTH_RQAOA — Recursive QAOA

- Source: Main Eq. (15), Appendix C pseudocode.
- Algorithm: select maximal absolute edge correlation, contract one variable,
  repeat to `n_c`, solve the remainder exactly, reverse all constraints.
- Parameters: `n_c=8` at `n=32`; `n_c=30` at `n=100`.
- Check: reconstructed and reduced-plus-shift energies agree at every completed run.
- Status: verified.

## MTH_EXACT — Exact signed Ising solver

- Source: definition of `E_max` in the Fig. 1 caption.
- Algorithm: binary XOR MILP with global spin-flip symmetry fixed.
- Check: agreement with exhaustive enumeration on a signed cubic eight-spin model;
  all production rows require zero reported optimality gap.
- Status: verified.

## MTH_RENDER — Rendering

- Source: visual contract of Main Fig. 1.
- Inputs: frozen CSV ratios only.
- Adjustable presentation: canvas, axes, font sizes, palette, bar width, legend.
- Forbidden adjustments: graph/coupling seeds, energies, ratios, beta/gamma, or
  any generated numerical array.
- Status: separated from scientific generation; original pixels are reference-only.
