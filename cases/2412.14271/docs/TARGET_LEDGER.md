# Target Ledger

`artifact_valid` means the declared output exists, its scientific checks pass,
and its isolated run is attested. It does not mean lifecycle `complete`.

| Target | Paper item | Fidelity | State | Data / figure | Scientific evidence | Remaining gap |
| --- | --- | --- | --- | --- | --- | --- |
| T001 | Fig. 2(a-g) | analytic exact; quantum feature-level | `artifact_valid` | `outputs/data/{analytic_branches,fig2_quantum}.npz`; `outputs/figures/fig2.png` | `fig2_science.json`, `fig2_quantum_science.json` | Finite-time trajectories replace paper ED at M=60/80/100. |
| T002 | Fig. 3(a-g) | feature-level, reduced trajectories | `artifact_valid` | `outputs/data/main_quantum.npz`; `outputs/figures/fig3.png` | `fig3_science.json`, `fig3_analytic_science.json` | 6-16 trajectories rather than paper production counts; N=5 uses QT rather than ED. |
| T003 | Fig. 4(a-f) | feature-level, reduced trajectories | `artifact_valid` | `outputs/data/main_quantum.npz`; `outputs/figures/fig4.png` | `fig4_science.json` | Four-lobe structure reproduced; finite sampling leaves Z4 residual 0.13-0.62. |
| T004 | Formal Fig. S1(a-b) / v1 Fig. 5(a-b) | printed-equation exact | `artifact_valid` | `outputs/data/analytic_branches.npz`; `outputs/figures/figS1.png` | `figS1_science.json` | Fresh-context review remains pending. |
| T005 | Formal Fig. S2(a-c) / v1 Fig. 6(a-c) | printed-equation exact with stable source discrepancy | `artifact_valid_with_discrepancy` | `outputs/data/analytic_branches.npz`; `outputs/figures/figS2.png` | `figS2_science.json`; `PAPER_DISCREPANCY.md` | The plotted lower branch is nonlinearly unstable, but it has no positive Bogoliubov eigenvalue; fresh review must test whether the formal supplement resolves the apparent root pairing. |
| T006 | Formal Fig. S3 and Formal Fig. S4, two separate items | unavailable | `blocked_missing_source_input` | — | `figure_coverage.json`; `outputs/checks/figure_coverage_check.json` | Formal supplement source, panel inventory, parameters, and observables could not be frozen. |
| T007 | Formal Fig. S5 / v1 Fig. 7 | reduced convergence diagnostic | `artifact_valid_reduced` | `outputs/data/main_quantum.npz`; `outputs/figures/figS5.png` | `figS5_science.json` | 4 vs 6-16 trajectories, not 500 vs 3000; max mean shift 21.30. |
| T008 | v1 parity supplement Fig. 8(a-c), formal numbering unverified | paper-exact parameters | `artifact_valid` | `outputs/data/figS_parity.npz`; `outputs/figures/figS_parity.png` | `figS_parity_science.json` | Two zero modes and exact parity preservation pass; fresh-context review pending. |

## Item-level Coverage

The public coverage denominator is not the eight implementation targets. It is
the independently adjudicable numerical content of the paper:

- eligible numerical items: **31**;
- covered items: **29**;
- uncovered items: **2**;
- item coverage: **29/31 = 93.55%**;
- mean fidelity of covered items: **48.23/100**;
- paper reproduction degree: **45.12/100**, computed as
  `coverage × covered-item fidelity`, with every uncovered item scored as zero.

The eight targets remain implementation groupings only. They must not make a
seven-panel figure count the same as a one-panel figure.

## Uncovered Items

| Uncovered item | Current missing evidence | Direct cause | Root-cause boundary | What closes it |
| --- | --- | --- | --- | --- |
| Formal Fig. S3, panel inventory unavailable | Formal caption, panel count, plotted observable, and printed parameters | Formal supplemental file is not present in the frozen source bundle. | **Source/input boundary**, not a demonstrated code error or compute shortage: APS required authorization on 2026-08-22, while arXiv v1 predates this formal-only figure. | Acquire and hash the formal supplement; enumerate its subpanels; derive each contract; only then decide whether existing code suffices or a numerical run is needed. |
| Formal Fig. S4, panel inventory unavailable | Formal caption, panel count, plotted observable, and printed parameters | Formal supplemental file is not present in the frozen source bundle. | **Source/input boundary**, not a demonstrated code error or compute shortage: the available accepted manuscript has no supplement, and v1 cannot prove this item's content. | Acquire and hash the formal supplement; enumerate its subpanels; derive each contract; only then decide whether existing code suffices or a numerical run is needed. |

No proxy panel, author numerical array, or guessed contract is accepted for
either item. The two rows remain visible and contribute zero until closed.

The authoritative lifecycle status remains `in_progress`, and the reproduction
level is `partial_reproduction`. Coverage is only one dimension: reduced-scale
targets, low-fidelity critical items, and pending independent review remain
separate constraints.
