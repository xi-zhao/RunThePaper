# Lessons Learned

## Case Summary

- Paper: Leveraging Qubit Loss Detection in Fault-Tolerant Quantum Algorithms.
- PaperID: `2502.20558`.
- Final status: numerical feature reproduction, 79.31/100; scientifically partial
  with 272/272 eligible atomic items finally resolved.
- Main reproduced targets: printed lifecycle-threshold relation, algorithm
  lifecycle counts, SWAP/conventional lifecycle invariants, Table-I analytic
  rows, and a delayed-erasure mechanism proxy.
- Final boundary: 245 items reached an attested clean-room system-capability
  limit; one Error Model B item is externally blocked by incompatible published
  definitions. Missing author code/data is not treated as the external blocker.

## What Worked

- Rendering all 27 source figures immediately made panel classification fast and
  avoided confusing plot assets with raw numerical data.
- The formula gate separated closed-form lifecycle/counting targets from
  circuit-level targets before implementation.
- A small proxy validated the key information-ordering feature without being
  promoted to a surface-code claim.
- Panel-level coverage allowed mixed figures to split schematic and numerical
  responsibilities cleanly.

## What Was Difficult

- The arXiv archive looks rich because it contains every vector figure, but it
  contains no data-generating program or tabulated samples.
- Several panels combine analytic trends, finite-size points, and architectural
  schematics; one figure-level status is too coarse without panel groups.
- Lifecycle boundary conventions and SWAP edge pairing are visually inferable
  but not sufficiently specified for `paper_exact` status.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Vector plot source is not numerical source | publication archives often bundle PDF/EPS plots only | inventory code/data/table assets separately from active figure assets |
| Proxy models need a permanent product state | a proxy can validate mechanism while failing absolute numerics | bind `proxy_model` to exploratory stage and an evidence-backed attempted-not-reproduced disposition |
| Mixed figures require panel contracts | schematic and numeric panels have different acceptance criteria | classify and score panel groups before coding |
| Missing fit metadata limits paper-exact adjudication | thresholds can shift with grids/windows even if curves look similar | require independently justified shot/grid/seed/fit cards before any future paper-scale launch |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Treating rendered vector curves as reproducible data | 27 clean PDFs could be mistaken for a data release | mark every rendered figure `source_figure_only` and prohibit it as a numeric input |
| Calling analytic subpanels a complete figure | Fig. 4(b), Fig. 16(a), and Table I mix analytic and simulation content | use panel ledgers and partial scope caps |
| Spending more compute on the wrong model | local proxy runs in under a second but cannot close the paper gap | run a bounded discriminator, classify the system capability limit, then stop |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Source-asset inventory before target design | any TeX/arXiv paper | distinguished 27 figures from zero code/data files |
| Formula-first local subset | simulation papers with printed analytic relations | yielded three final paper-exact artifacts |
| Side-by-side source/generated boards | partial visual/feature validation | exposed correct shapes and large proxy scale differences immediately |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| `vector_archive_false_completeness` | arXiv source had all plot PDFs but no samples/code | inventory extensions and search for actual generators/tables before declaring source complete |
| `analytic_overlay_scope_inflation` | a printed fit can match while simulation markers remain unavailable | require panel ledger and separate analytic/reference provenance |
| `proxy_absolute_curve_leakage` | a mechanism proxy could visually resemble Fig. 2(b) | hard-bind proxy to exploratory stage and include absolute-curve-claimed=false check |
| `scaffold_registry_identity_split` | the scaffold wrote `metadata/case.yaml` but the homepage registry reads root `CASE_META.json` | make the scaffold create both identity views and cover the registry card with a regression test |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| arXiv source scientific-input inventory | detects code, tables, benchmark data, and figure-only archives | `PRAgent-workflow/scripts/inspect_source_assets.py` |
| mixed-panel coverage helper | reduces manual JSON errors for schematic/numeric panel splits | extend `build_paper_map.py` or case scaffold |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| vectorized repetition-code proxy | 800,000 shots across four depths in 0.66 s with all targets | keep case-local; it is not a surface-code model |
| closed-form lifecycle endpoint counting | instant, deterministic, fully tested | keep formula local; promote only after a second compatible QEC case |

## Harness Backlog Items

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| medium | add source scientific-input inventory distinct from figure rendering | 27 vector assets and zero numerical sources | `copied_to_backlog` |
| high | make every scaffolded case immediately discoverable by the registry | this case was absent from the homepage despite a complete workspace | `copied_to_backlog` |

## Prompt Or Workflow Changes

- After rendering source figures, explicitly report counts for code files, raw
  numerical tables, benchmark inputs, and figure-only assets.
- Do not ask for more wall time when the current system lacks the required model;
  run a bounded clean-room discriminator and record the capability limit.
