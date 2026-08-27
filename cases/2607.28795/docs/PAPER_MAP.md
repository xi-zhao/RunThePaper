# Paper Map

## Identity

- Paper ID: `arXiv:2607.28795v1`
- Title: *High-rate qLDPC processors*
- Authors: Aditya Bhardwaj, Muzhou Ma, Nadine Meister, Robbie King, Dolev
  Bluvstein, John Preskill, Madelyn Cain, Qian Xu, and Hsin-Yuan Huang
- Source: <https://arxiv.org/abs/2607.28795>
- Local PDF: `raw/paper.pdf`
- PDF SHA-256: `4ac964874e5c49e8d02a284b6a877f590927e61523fe7f086d7b5f8bff2b7d2e`
- Version/date: v1, 30 July 2026; PDF dated 3 August 2026
- Formal publication: unpublished preprint as of case creation (4 August 2026)
- Author implementation: declared open-source by the paper, deliberately not
  opened, cloned, downloaded, or used; see `author_code_policy.json`.

## Reproduction Goal

Independently reconstruct the scientific objects that are both specified in
the paper and bounded enough to run in minutes to hours:

1. the group-algebra lifted-product check matrices of the eight mitten codes;
2. CSS commutation, rank, 20% encoding rate, check weight, square
   invertibility, and canonical logical-operator weights;
3. the closed-form parallel-magic-injection resource counts in Table V;
4. a reduced, independently written validation and benchmark of the sQetch
   sketch-ISD algorithm in Appendix H;
5. the arithmetic real-time consistency test of Eq. (I1) and Table X.

The billion-shot decoder experiments, the `10^12`-trial discovery benchmark,
and numerical objects whose exact circuits, schedules, gadget graphs, or
optimized layouts exist only in the forbidden author repository are recorded
as explicit deferred targets. Paper scalars may be used as comparison or as
declared inputs to a derived consistency calculation, never as generated
simulation data.

## Paper Structure

| Section | Role | Reproduction consequence |
| --- | --- | --- |
| I-II | Processor motivation and metrics | Defines processing capacity, throughput, and cycle time. |
| III | Mitten codes | Core algebraic target: Eqs. (1)-(4), Table I. |
| IV / App. C-E | Fault-tolerant gadgets | Closed-form Table V is reproducible; optimized gadget instances are not fully specified. |
| V / App. I | Circuit-level simulations and telescoping decoder | Paper-scale runs are deliberately deferred. |
| VI / App. J | Neutral-atom and superconducting layouts | Formula trace is retained; exact optimized layouts are missing from the PDF. |
| VII / App. F-H | Discovery pipeline and sQetch | Algorithm 1 is independently implementable at reduced scale. |
| App. A-B, G | LP algebra, canonical basis, distance bounds | Supplies derivations and sanity checks for the code constructor. |
| App. K | Construction data | Table XIII is a paper parameter source, not generated result data. |

## Equation/Method Inventory

| ID | Source | Role | Initial status |
| --- | --- | --- | --- |
| Q001 | Eqs. (1)-(2), (A18)-(A19), (J1) | Build mitten-code `H_X,H_Z` from group-ring entries | source traced |
| Q002 | Eqs. (3)-(4), Theorems 1 and 4 | Construct the canonical logical basis | source traced |
| Q003 | Eqs. (A25)-(A26), (F1) | Compute `n,k` and rate | source traced |
| Q004 | Eqs. (E15), Theorem 7 | Parallel magic-injection counts and distance guarantee | source traced |
| Q005 | Eqs. (H1)-(H8), Algorithm 1 | Independent sQetch estimator | source traced |
| Q006 | Eqs. (H9)-(H13) | Hit-probability sanity checks | source traced |
| Q007 | Eq. (I1), Table X | Decoder utilization and mean reaction time | source traced |
| Q008 | Eqs. (J2)-(J3) | Group-action atom permutations | source traced; exact schedules absent |
| Q009 | Eqs. (J8)-(J10) | Layout cost and spectral placement | source traced; HAL routing absent |

## Figure Inventory

| Item | Content | Class | Decision |
| --- | --- | --- | --- |
| Fig. 1 | Code/gadget overview | schematic | exclude |
| Fig. 2(a) | Memory logical-error curves | numerical Monte Carlo | defer: billions of shots and exact circuits/schedules unavailable |
| Fig. 2(b) | Surgery shots and logical errors | numerical Monte Carlo | defer: up to 15 billion experiments |
| Fig. 3 | Discovery workflow | flowchart | exclude |
| Fig. 4 | Hardware mapping cartoons | schematic | exclude |
| Fig. 5 | Surgery gadget graphs | schematic | exclude |
| Fig. 6 | Magic-state injection scheme | schematic | exclude; Table V carries the numeric target |
| Fig. 7 | Symbolic block matrices | derivation diagram | exclude |
| Fig. 8 | sQetch benchmark | numerical benchmark | T003 reduced-scale, independently implemented |
| Fig. 9 | Decoder comparison | numerical Monte Carlo | defer: benchmark DEM/config plus billions of shots |
| Figs. 10-11 | Example atom movements | schematic | exclude |
| Fig. 12 | SE cycle-time scatter | numerical optimization | defer: exact schedules/layouts only in forbidden repository |
| Fig. 13 | Tanner-graph decomposition | schematic proof | exclude |

## Table Inventory

| Item | Content | Decision |
| --- | --- | --- |
| Table I | Mitten-code summary | T001 for algebraic columns; other columns covered by their detailed deferred tables |
| Tables II-IV | Optimized surgery/extractor instances | defer: exact gadget graphs and random instances absent |
| Table V | Parallel magic-injection counts | T002 exact closed-form reproduction |
| Table VI | Processor code parameters | T001 for mitten-code algebraic rows |
| Table VII | Group definitions | parameter source, not a result target |
| Table VIII | Circuit-level distances | defer: exact schedules only in author repository |
| Table IX | Decoder benchmark | defer: external DEM and billion-shot run |
| Table X | Real-time analysis | T004 formula-level arithmetic consistency |
| Table XI | Atom-array SE metrics | defer: optimized layouts/schedules absent |
| Table XII | HAL hardware complexity | defer: routed layouts and heuristic seeds absent |
| Table XIII | Base matrices | parameter source for T001, not generated data |

## Assumptions and Hard Boundaries

- GAP 4.16.0 and SmallGrp 1.5.4, exactly as cited in references [113]-[114],
  are independent mathematical dependencies used only to interpret the group
  IDs and element ordering printed in Tables VII and XIII.
- The literal Table-XIII interpretation exposes a construction-data
  inconsistency: the `(60,11)` pivot entries are singular. No hidden element
  remapping is inferred from the reported logical weights.
- No arXiv source bundle is ingested because it could contain generated data or
  implementation artifacts; the PDF is the sole paper input.
- No repository URL is opened. The locator is recorded only because it appears
  in the PDF.
- Large runs allowed to be skipped by the user remain visible in
  `figure_coverage.json`; they are not counted as reproduced.
- Any figure renderer consumes only independently frozen arrays. It cannot read
  `raw/` or an original-figure directory.
