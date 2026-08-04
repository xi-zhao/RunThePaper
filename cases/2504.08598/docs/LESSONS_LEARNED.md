# Lessons Learned

## Case Summary

- Paper: *Graph coloring via quantum optimization on a Rydberg-qudit atom array*.
- PaperID: `2504.08598`.
- Final status: central numerical feature reproduction with evidence caps.
- Main targets: Figures 5-6 and the graph/controls handoff.
- Main blockers: Figure 7 source conflict; appendix numeric mismatches; no
  equivalent public Pasqal multilevel backend.

## What Worked

- Freezing the final published PDF and official author CSV ZIP removed version
  ambiguity.
- Generating first, then opening author data, protected independence.
- Separating paper-selected target states from all proper colorings made graph
  F's symmetry claim testable.
- Sparse exact evolution kept every disclosed small graph CPU-feasible.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| backend equivalence precedes cross-validation | two simulators can agree while solving different Hamiltonians | define Hilbert space, interactions and controls before naming a second backend |
| source tables can contain coordinate-scale conventions | a silent factor changes every C6/R6 term | test physical distances against text/blockade constraints |
| distribution ordering is not a semantic observable | unspecified basis order can inflate pointwise TVD | retain raw TVD but also compare invariant sorted mass and decoded solution mass |
| main and appendix gates need separate verdicts | one appendix mismatch should not erase a reproduced central claim | publish named per-target failures and a bounded central verdict |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| treating Pasqal availability as automatic validity | public Pulser uses a qubit local space | require same local dimension and interaction matrix |
| calling all proper colorings the plotted target | graph F plots a dominant symmetry pair | derive target semantics from caption/data and retain broader validity separately |
| silently choosing a conflicting parameter | Figure 7 protocol-c Omega differs by source location | freeze as `missing_source_input` |
| scaling tetrahedron coordinates literally | edge length becomes sqrt(2) too large | record interpretation and unit-test the physical edge |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| `backend_hilbert_space_mismatch` | Pasqal qubit backend versus EV20 qudit model | compare local dimension and interaction channels before running |
| `source_parameter_conflict` | Figure 7 protocol-c Omega | require one authoritative value or freeze `missing_source_input` |
| `undisclosed_basis_indexing` | author distribution CSVs | compare raw and permutation-invariant observables separately |
| `coordinate_scale_semantic_conflict` | tetrahedron Table 1 versus Table 2 | compute all physical edge lengths and check the prose/blockade constraints |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| backend-equivalence contract | prevents false dual-backend validation | platform validation layer |
| semantic distribution metrics | invariant to undisclosed basis ordering | harness comparison utilities |
| geometry-distance audit | catches coordinate/spacing inconsistencies | hardware compiler validation |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| cached sparse drive/diagonal operators | complete 4096-state case runs locally | generic pattern, case-local implementation |
| cached graph/profile results across panels | avoids duplicate evolutions | promote comparison orchestration pattern |

## Harness Backlog Items

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| high | explicit `not_applicable_backend` validation state | Pasqal qubit model is inequivalent | proposed |
| medium | semantic distribution comparison schema | source basis ordering absent | proposed |
| medium | source-conflict blocker with two citations | Figure 7 protocol-c | proposed |

The cross-paper items above were copied_to_backlog under case `2504.08598`.

## Prompt Or Workflow Changes

Before asking a second simulator to “verify” a result, require an explicit
machine-readable equivalence check for local Hilbert space, Hamiltonian terms,
units, time controls, initial state and measured observable.
