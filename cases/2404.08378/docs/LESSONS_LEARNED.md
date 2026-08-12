# Lessons Learned

## Case summary

- Paper: *On-Chip Quantum Interference between Independent Lithium Niobate-on-Insulator Photon-Pair Sources*.
- Paper ID: `2404.08378`.
- Current status: partial / review pending.
- Main result: 18 independent numerical targets; central two-photon interference physics supported.
- Main blockers: nine unpublished experimental arrays, incomplete vector-FEM settings, fresh-context review.

## What worked

- Lifting the printed 2×2 MZI matrix to a 3×3 two-boson representation provided one compact model for Main Figs. 2–3 and Supplement Figs. S1–S2.
- Limiting cases and unitarity checks were stronger and cheaper than trying to match plot styling.
- Strict CSV schemas made the unavailable experimental path executable without inventing data.
- Freezing numerical hashes before any source-figure access kept visual optimization separate from scientific inference.

## What was difficult

- The paper combines theory surfaces, experimental points, device simulations and rounded text claims; coverage must be classified per component, not per whole figure.
- A stated HOM width can map to different bandwidths depending on convention.
- Published device figures do not supply enough vector-FEM detail for paper-exact reconstruction.
- Disk was temporarily dominated by duplicate BagIt extraction and page renders; reproducibly downloadable duplicates were removed while hashed source artifacts were retained.

## Generalized lessons

| Lesson | Why it generalizes | Future rule |
| --- | --- | --- |
| isolate numerics from rendering | plotting libraries may spawn font-cache subprocesses and pollute access attestations | scientific runners emit arrays/checks only; rendering gets a separate contract |
| classify mixed panels by component | a theory curve may be reproducible even when measurements are not public | enumerate theory and experimental components separately |
| width conventions are parameters | silent convention choices can create artificial agreement | output all plausible named conventions and keep the target partial |
| missing author data is not compute debt | more CPU/GPU cannot recover unpublished arrays | code the ingestion path, then fail closed |
| proxy solver must be explicit | a plausible scalar model is not the unpublished vector FEM | cap status/score and record indispensable missing settings |

## New Failure Modes

The first isolated attempt included Matplotlib. Font discovery attempted subprocesses and was correctly blocked. The response was architectural: remove all rendering from the numerical entrypoint, rerun isolation, freeze hashes, then render. The successful v2 run recorded zero denied/forbidden accesses.

## Reusable Checks Or Tools

| Priority | Improvement | Evidence | Status |
| --- | --- | --- | --- |
| high | make numerics-only runner plus post-freeze RenderContract the default template | v1 failed and v2 passed after separation | case proven; Harness promotion recommended |
| high | require component-level classification for mixed experimental/theory panels | nine arrays remain unavailable while 18 theory targets are valid | case proven |
| medium | add a convention-audit field for reported widths/normalizations | 71.9 fs and brightness normalization are definition-sensitive | case proven |
| medium | report transient/raw disk duplication before starting new cases | local disk was close to full | case-local cleanup completed |

No global Harness file is changed from this case branch; these items remain explicit backlog recommendations rather than hidden cross-case edits.
