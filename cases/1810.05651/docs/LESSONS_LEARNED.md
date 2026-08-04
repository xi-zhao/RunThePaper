# Lessons Learned

## Case Summary

- Paper: *Probing context-dependent errors in quantum processors*
- PaperID: `1810.05651`
- Final result: complete numerical reproduction
- Targets: Figure 2 simulated drift and Figure 3 IBM crosstalk
- Blockers: none

## What Worked

- Reading the frozen source bundle before implementing exposed complete count
  files and paper-exact circuit selections.
- A small independent statistical core reproduced both targets without
  executing author notebooks or importing their pyGSTi analysis.
- Separating data generation, scientific checks, rendering, and comparison made
  provenance and failure location explicit.
- Integer-count assertions caught the sample scale and field semantics before
  any visual comparison was trusted.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Recompute from released raw counts | A redraw alone cannot validate the analysis | Treat author counts as inputs and independently implement observables |
| Verify display conventions separately | Source plots can differ from printed equations | Store scientific values and source-compatible display values in separate fields |
| Use set identity for unordered circuit collections | Serialization order is not a physical invariant | Test membership and multiplicity unless order is part of the method |
| Preserve exact fractions behind formatted labels | Paper labels may truncate or round inconsistently | Score exact structured data; use source labels only for pixel comparison |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | Prevention |
| --- | --- | --- |
| Treating `0 log 0` as an error | Some pooled outcomes are absent | Implement the continuous multinomial limit explicitly |
| Applying one decimal rule to every label | Figure 2 mixes integers and one-decimal labels | Declare the source display contract independently of scientific tolerance |
| Conflating reanalysis with new acquisition | IBM hardware data are historical | State the provenance boundary in checks, reports, and scorecard |
| Optimizing pixels before science | Styling can conceal wrong data | Require passing scientific assertions before rendering and comparison |

## New Failure Modes

| Failure mode | Where it appeared | Detection |
| --- | --- | --- |
| Exact source normalization disagrees with the printed equation | Figure 2 notebook ordinate | Compare the code-defined quantity with an independent equation-level identity before rendering |
| Source labels do not follow ordinary rounding | Figure 3 labels 12.98828125% as 12.9% | Keep exact values in structured data and test source labels as a separate display contract |
| Valid circuit collections serialize in different orders | Figure 3 LGST inputs | Compare canonical multisets unless the paper gives order physical meaning |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| Equation-to-source scale-factor check | Detects plotting-code normalization artifacts without weakening science | Future harness backlog after this frozen Trial |
| Exact-count sample-scale validator | Prevents incomplete author datasets from passing visual checks | Case adapter helper or future generic checker |
| Structured-value/display-label split | Supports honest science and pixel fidelity simultaneously | Future figure contract guidance |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Scope |
| --- | --- | --- |
| Vectorized count-table analysis | T001 scientific run `1.709 s` for 1405×5 pools | Case-local |
| Direct integer SSTVD calculation | T002 scientific run `0.465 s` for all 7 rungs | Case-local |
| Tar-member streaming | No source extraction tree or notebook runtime needed | Case-local |

## Harness Backlog

No frozen harness file was changed in this Trial. A possible future generic
check is to compare equation-defined normalization against released plotting
code and classify exact scale factors as source artifacts rather than silently
adopting them. `copied_to_backlog: false` because the Trial protection boundary
explicitly forbids modifying `private validation harness`.
