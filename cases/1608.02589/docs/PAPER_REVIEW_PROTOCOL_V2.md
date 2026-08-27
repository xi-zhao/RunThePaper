# Paper Review Protocol v2

This case reproduces physics and audits the paper at the same time. A numerical mismatch is not automatically a paper error.

## Ordered attribution

1. Reproduction defect: check Hamiltonian signs, operator order, observables, boundary conditions, disorder sampling, aggregation, and rendering.
2. Numerical limitation: check finite size, finite time, disorder count, eigensolver selection, precision, and convergence.
3. Missing or ambiguous paper input: identify unpublished seeds, grids, fit weights, protocol details, or author realization data.
4. Potential paper discrepancy: only after the first three explanations are actively falsified may a stable contradiction enter fresh-context review.

Every potential discrepancy must identify the exact equation/caption/claim, provide at least two scientifically distinct strong checks where feasible, state its impact, and survive an inventory-first reviewer who did not see the original reproduction conversation.

## Current audit state

- Paper-error candidates: `0`.
- The acknowledgement says a prior manuscript version omitted coupling-strength disorder from Eq. (1), while the simulations already used it. The reviewed version includes the term, so this is author-disclosed history, not a newly discovered error.
- Supplement Fig. S1(c) leaves some implementation details of the susceptibility implicit. The case declares one text-faithful interpretation and keeps it `reconstructed`; a quantitative difference cannot be assigned to the paper without ruling out alternative interpretations.
- Exact epsilon meshes, seeds, phase-boundary weighting, some disorder counts, and matrix-free sampling choices are not printed. These block pointwise paper-exact claims even if the qualitative physics agrees.
- The full paper-scale campaign has not run. Smoke execution proves code reachability and invariants only; it cannot validate the published critical exponents or phase boundaries.

## Review boundary

A fresh-context review bundle may be generated after the implementation, provenance, formula cards, coverage inventory, and numerical evidence are frozen. Until an independent reviewer returns a valid protocol-v2 decision, the authoritative state must remain incomplete and `paper_error_candidate_emitted` must remain false.
