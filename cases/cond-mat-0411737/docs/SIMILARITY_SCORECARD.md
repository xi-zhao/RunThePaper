# Similarity Scorecard

## Case result

- Artifact quality score: **88.85/100** (`passed`), reported separately from
  scientific adjudication and lifecycle state.
- Similarity level: `numerical_feature_reproduction`.
- Scientific assertions: **13/13 target gates passed**; the runner records 40
  passed checks and no failed check. The scorecard projects 32 essential
  assertions onto the 13 targets; eight additional checks are lower-level
  invariants and active falsification checks.
- Scientific-region pixel score for Main Fig. 1: **90.3679/100**, classified
  `high_fidelity`.
- Full-canvas score: **89.3059/100**, used only as a layout diagnostic.

The number above summarizes declared evidence and visual fidelity; it is not a
substitute for scientific review. Seven targets are paper-exact and six are
evidence-capped. The v18 fresh-context review passed with complete scope: 104
claims are supported, ten are inconclusive, and no reproduction defect or
paper-error candidate remains.

## Target scores

| Target | Scientific object | Parameter match | Score |
| --- | --- | --- | ---: |
| T001 | Main Fig. 1 bands, armchair/flat-band boundary tests | paper subset | 80 |
| T002 | continuum Dirac spectrum and intrinsic gap | paper exact | 90 |
| T003 | Rashba boundary plus declared conventional-current Kubo proxy | paper subset | 89 |
| T004 | spin Chern topology plus explicitly bounded mass-path proxy | paper subset | 89 |
| T005 | finite-cylinder flux pump | paper subset | 89 |
| T006 | Kramers protection and random scalar disorder | paper exact | 90 |
| T007 | interaction operator and independently fitted exponents | paper exact | 90 |
| T008 | Fig. 2(a) two-terminal conductance | paper exact | 90 |
| T009 | Fig. 2(b) four-terminal spin current | paper exact | 90 |
| T010 | explicit first-star matrix and intrinsic-SO estimate | paper subset | 89 |
| T011 | electric-field Rashba estimate | paper subset | 89 |
| T012 | one-loop shell, screening and Coulomb RG flow | paper exact | 90 |
| T013 | self-consistent enhanced gap | paper exact | 90 |

T001 is capped at 80 by the conservative `visual_feature_contract` evidence
tier. Its measured scientific-region pixel score is higher, but the source
does not publish the ribbon width or plotting grid, so the scorecard does not
promote it to paper-exact.

## Pixel interpretation

| Pixel target | Role | Score | Lifecycle use |
| --- | --- | ---: | --- |
| PXT_T001_LEFT_BANDS | primary scientific region | 90.3679 | eligible |
| PXT_T001_FULL_DIAGNOSTIC | full canvas | 89.3059 | diagnostic only |

The primary region contains the full symmetry-unique half of the band plot.
Its foreground-only similarity is 32.3951 and the generated/source line-density
ratio is 0.711. Those lower foreground diagnostics are retained because they
show the remaining branch-density difference caused by the unreported finite
strip width; they are not hidden by the background-weighted score.

## Causal diagnosis

| Targets | Direct cause | Root cause | Code-fault status |
| --- | --- | --- | --- |
| T001 | finite ribbon width and k-grid are absent | publication underspecified | not found after unit, invariant, convergence and isolated-run checks |
| T003 | exact conserved-spin-current operator is unavailable | publication underspecified | adaptive full-k edge-overlap tracking now supports every declared subcritical zigzag and armchair branch at three widths; the conventional-current response remains explicitly proxy-only |
| T005 | finite cylinder circumference, cutoff and flux grid are not published | publication underspecified | not found after explicit spectral-flow and topological-invariant checks |
| T004 | a uniform-field microscopic bulk bridge is not supplied | publication underspecified | edge gap supported; intervalley path explicitly proxy-only; the minimal translation-preserving published-term candidate is independently falsified by a continuous gap closure |
| T010 | numerical lattice constant behind the rounded estimate is absent | publication underspecified and exactness overclaim | arithmetic code is correct; provenance is not paper-exact |
| T011 | numerical Fermi velocity behind the rounded estimate is absent | publication underspecified and exactness overclaim | arithmetic code is correct; provenance is not paper-exact |
| T012 | no remaining causal blocker | independent calculation repaired | Lindhard generator plus angular/UV convergence replaces circular input |

The current causal diagnoses are terminal publication/external-input
boundaries, not hidden code failures. Three external-input claims remain
separately deferred and do not enter the 13-target score. The validated v18
review independently tested the repairs; nothing was promoted merely because
the runner passed.

Machine-readable record:
`outputs/checks/similarity_scorecard.json`.
