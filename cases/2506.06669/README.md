# 2506.06669: Remote entanglement generation via enhanced quantum state transfer

Preprint: [arXiv:2506.06669 — Remote entanglement generation via enhanced quantum state transfer](https://arxiv.org/abs/2506.06669)

Published as: [Remote Entanglement Generation Via Enhanced Quantum State Transfer](https://doi.org/10.1103/4x8d-cmyx)

Formal citation: PRX Quantum 7, 010348 (2026) · DOI `10.1103/4x8d-cmyx` · Locator `010348`

Public status: **Partial scientific reproduction** · Audit score: **70.23/100**

Fifty-five of sixty whole-paper reproduction items have accepted evidence; Supplement Fig. S10(a) and four no-display analytic claims remain uncovered.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Equation-level derivation](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Public evidence index](docs/EVIDENCE_INDEX.md)
- [Comparison policy](docs/COMPARISON_POLICY.md)
- [Scientific consistency report](docs/CONSISTENCY_REPORT.md)
- [Independent paper assessment](docs/PAPER_ASSESSMENT.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Paper Reference vs Independent Reproduction

Each board contains only the minimum paper excerpt needed for validation and places it beside an independently generated result. Visual agreement is a scientific-region diagnostic, not author-data-level equivalence.

### T001 fig1cd board comparison

![T001 fig1cd board paper reference versus independent reproduction](docs/comparisons/T001_fig1cd_board.png)

### T002 figS3 board comparison

![T002 figS3 board paper reference versus independent reproduction](docs/comparisons/T002_figS3_board.png)

### T002 solution board comparison

![T002 solution board paper reference versus independent reproduction](docs/comparisons/T002_solution_board.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2506.06669/code
python scripts/run_reproduction.py --config config/smoke.json
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 3 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, parameters=mixed, causal_resolution=repair_required, science=failed, pixel=needs_repair, paper_assessment=inconclusive.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![T001 fig1cd](outputs/figures/T001_fig1cd.png)

![T002 figS3](outputs/figures/T002_figS3.png)

![T002 solution](outputs/figures/T002_solution.png)

![T003 fig2def](outputs/figures/T003_fig2def.png)

![T004 fig3ab](outputs/figures/T004_fig3ab.png)

![T005 fig3cd](outputs/figures/T005_fig3cd.png)

![T006 figS8def](outputs/figures/T006_figS8def.png)

![T007 fig4 theory](outputs/figures/T007_fig4_theory.png)

![T008 figS7def](outputs/figures/T008_figS7def.png)

![T009 figS9](outputs/figures/T009_figS9.png)

![T010 figS10](outputs/figures/T010_figS10.png)
