# Lessons Learned

## Case Summary

- PaperID: `10.1103-PhysRevLett.124.113601`.
- Final status: 88.56/100, numerical feature reproduction; Fig. 3 complete reproduction.
- Reproduced: Figs. 2–4, Supplement Fig. S1, and finite-size/trap diagnostics.
- Main blockers to complete reproduction: author data, a detuning-convention inconsistency, omitted nonlinear continuation details, and omitted S1 pump samples.

## What Worked

- Formula cards and the formula gate exposed the factor-of-two detuning ambiguity before it could silently contaminate all targets.
- Target-local boundary conditions fixed the Fig. 2 edge-state artifact without damaging the open-chain S1 density target.
- Structured CSV-first generation made every figure traceable and enabled numeric checks independent of plotting.
- Descending-pump continuation recovered the symmetry-broken nonlinear branch and the source photon-number endpoints.
- Sparse/tridiagonal solvers made the full M4 reproduction a seconds-scale job, including `L=10000` diagnostics.
- Extracting vector paths from the original PDFs exposed a hidden Fig. 2 finite-chain convention and enabled real pointwise checks without contaminating generated data.

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | Prevention |
| --- | --- | --- |
| One global convention for every panel | factor 2 matches linear curves but fails nonlinear curves | allow target-local conventions with explicit source evidence |
| One global boundary condition | open Fig. 2 creates four source-absent edge spikes | treat boundary as target metadata and test visible artifacts |
| Rational finite-size alias | `gamma_c=0.5` merges opposite momentum channels | retain raw finite-chain value and record a thermodynamic-limit display correction |
| Direct near-critical fixed point | 1000 iterations left five points unresolved | continuation plus residual checks and a 5000-iteration ceiling |
| Guessing S1 pump values from “above threshold” | using `eta=0.25` over-localized three panels by an order of magnitude | calibrate only missing samples to explicit visual landmarks and label `paper_subset` |
| Pixel similarity on independent replots | would produce meaningless low SSIM | add a paper-geometry renderer first, then run the Harness crop/evidence gates |
| Treating a caption approximant as the actual source curve | `233/377` produced a visibly jagged IPR mismatch | compare vector-path samples; use the exact golden ratio when it is the curve-producing convention |

## Generalized Experience

| Lesson | Why it generalizes | Recommendation |
| --- | --- | --- |
| Conventions can be panel-local | paper versions/captions may not share the same implementation convention | record convention scope in the target contract, not only global config |
| Source artifacts can diagnose hidden numerics | boundary conditions and aliases are often absent from prose | compare physical landmarks before styling |
| More compute cannot repair missing metadata | this full case runs in under 20 s | separate compute blockers from parameter/provenance blockers |
| Visual calibration is legitimate only as reconstruction | missing plotted samples sometimes can be bounded from axes | preserve a `paper_subset` stage and record the calibration landmark |
| PDF vector paths are stronger than screenshots | they preserve pointwise curve coordinates even without author CSVs | use them as reference-only evidence and record that they never feed generation |

## Reusable Checks Or Tools

| Candidate | Value | Destination |
| --- | --- | --- |
| target-local convention conflict detector | prevents a global parameter from forcing incompatible panels | Harness backlog H068 |
| finite-rational alias check | detects merged `+q/-q` channels at commensurate points | keep case-local until a second quasiperiodic case needs it |
| labelled non-pixel comparison board | already domain-neutral and follows independent-replot policy | existing Harness comparison workflow |

## New Failure Modes

| Failure mode | Detection |
| --- | --- |
| `cross_target_convention_conflict` | two independently validated panels require different source-traceable conventions |
| `finite_chain_momentum_alias` | isolated grid point violates the two-sided limit while neighboring points converge |
| `source_calibrated_missing_sample` | a parameter is chosen from visible source landmarks because the paper omits it; force exploratory stage |

## Harness Feedback

The abstract lesson was added to `PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`. Concrete convention-scope support is tracked as H068 in `PRAgent-workflow/HARNESS_BACKLOG.md`.
