# Lessons Learned

## Case Summary

- Paper: *Demonstrating quantum error mitigation on logical qubits*.
- PaperID: `10.1038-s41467-025-67768-4`.
- Final status: numerical feature reproduction; lifecycle incomplete.
- Main reproduced targets: repetition-code ZNE, distance-3 surface-code logical
  channel, complete ZNE proxy, large-scale logical memory and Table 3 audit.
- Main blockers: omitted calibration/decoder contracts, T001 source mismatch,
  fresh-context review pending.

## What Worked

- Freezing structured numeric arrays before viewing/cropping figures kept
  physics changes separate from presentation changes.
- Exact enumeration gave strong falsification checks without Monte Carlo.
- A full-paper item inventory prevented experimental schematics from being
  presented as numerical reproduction.
- Registered SSIM was useful for pure numerical figures, while explicit N/A
  status avoided meaningless pixel scores on experiment-mixed panels.

## What Was Difficult

- Paper prose can be internally inconsistent with a plotted simulation even
  when the independently derived formula and exhaustive enumeration agree.
- Median device errors are not a substitute for a per-gate calibration map.
- A table caption may state an exact invariant that its printed values satisfy
  only approximately.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Treat source alignment as a falsification gate | Correct code can expose a paper/model inconsistency | keep analytic truth and source alignment as separate assertions |
| Freeze all numerical subpanels, including geometric state scans | Render-time derivation can silently expand scientific scope | enumerate Bloch/state/grid arrays before the final isolated run |
| Distinguish missing metadata from insufficient compute | GPUs cannot infer an omitted decoder or schedule | require an executable benchmark contract before remote runs |
| Test captions numerically | “fixed”, “constant”, or “same” may be approximate | turn every table invariant into a machine check |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Calling a literal submodel paper-exact for the whole panel | T001 injection formula omitted the plotted simulator convention | define parameter match at the scored figure level |
| Scoring mixed panels with full-image SSIM | experimental markers cannot be regenerated scientifically | use a two-panel feature board and `pixel_status=not_applicable` |
| Assuming displayed values are rounded exact solutions | Table 3's 9.4 and 7.2 do not follow the exact schedule | compare exact and printed schedules explicitly |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Literal-formula plus exhaustive enumeration | small Pauli circuits | T001 closed form agrees with all 64 patterns |
| Exact Pauli-channel preclassification | small stabilizer codes | T004 enumerates `4^9` errors in a sub-second full run |
| Separate numeric freeze and RenderContract | every figure reproduction | style optimization changed no data hashes |
| Per-paper-item scorecard | multi-panel papers | weak T001 remains visible instead of being averaged away |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| `prose_curve_inconsistency` | Main Fig. 2(c) | compare literal formula endpoints against source trend after freeze |
| `approximate_invariant_presented_as_exact` | Supp. Table 3 | calculate invariant spread and rounding intervals |
| `numeric_subpanel_missing_from_freeze` | first T004 freeze omitted Bloch-circle arrays | require panel-to-array coverage before freezing |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| invariant-versus-rounded-table checker | detects false exactness claims | harness scientific checks |
| post-freeze mixed-panel comparison board | preserves experiment/theory boundary | harness comparison tools |
| render-style whitelist tied to numeric freeze hash | prevents physics changes during pixel tuning | harness RenderContract |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| exact distance-3 CSS Pauli classifier | full case in 0.796 s | case-local code; promote interface pattern only |
| distance-aware Vandermonde solve | residual below `1.2e-13` | promote generic helper |

## Harness Backlog Items

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| P1 | add panel-to-frozen-array coverage gate | Bloch circles were caught only during render audit | copied_to_backlog |
| P1 | add exact-vs-approximate table invariant checker | Table 3 caption overstates exactness | copied_to_backlog |
| P2 | add first-class two-panel N/A comparison builder | seven mixed panels needed a case-local script | copied_to_backlog |

## Prompt Or Workflow Changes

- Before numeric freeze, ask: “Does every theory-bearing subpanel have a
  declared frozen array, including geometric sweeps?”
- After freeze, make source-curve disagreement a scientific finding; never
  tune physics parameters in the rendering channel to erase it.
