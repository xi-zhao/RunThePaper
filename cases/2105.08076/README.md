# 2105.08076: Measurement-Induced Dark State Phase Transitions in Long-Ranged Fermion Systems

Preprint: [arXiv:2105.08076 — Measurement-Induced Dark State Phase Transitions in Long-Ranged Fermion Systems](https://arxiv.org/abs/2105.08076)

Published as: [Measurement-Induced Dark State Phase Transitions in Long-Ranged Fermion Systems](https://doi.org/10.1103/PhysRevLett.128.010605)

Formal citation: Phys. Rev. Lett. 128, 010605 (2022) · DOI `10.1103/PhysRevLett.128.010605` · Locator `010605`

Public status: **Partial scientific reproduction** · Audit score: **62.76/100**

All nine numerical panels are independently generated; failed targets are reported from their declared paper-defined scientific checks, and the paper-scale A100 campaign remains unrun.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Equation-level derivation](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Public evidence index](docs/EVIDENCE_INDEX.md)
- [Comparison policy](docs/COMPARISON_POLICY.md)
- [Scientific consistency report](docs/CONSISTENCY_REPORT.md)
- [Paper review protocol](docs/PAPER_REVIEW_PROTOCOL_V2.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Paper Reference vs Independent Reproduction

Each board contains only the minimum paper excerpt needed for validation and places it beside an independently generated result. Visual agreement is a scientific-region diagnostic, not author-data-level equivalence.

### T001 source vs reproduction comparison

![T001 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T001_source_vs_reproduction.png)

### T002 source vs reproduction comparison

![T002 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T002_source_vs_reproduction.png)

### T003 source vs reproduction comparison

![T003 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T003_source_vs_reproduction.png)

### T004 source vs reproduction comparison

![T004 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T004_source_vs_reproduction.png)

### T005 source vs reproduction comparison

![T005 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T005_source_vs_reproduction.png)

### T006 source vs reproduction comparison

![T006 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T006_source_vs_reproduction.png)

### T007 source vs reproduction comparison

![T007 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T007_source_vs_reproduction.png)

### T008 source vs reproduction comparison

![T008 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T008_source_vs_reproduction.png)

### T009 source vs reproduction comparison

![T009 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T009_source_vs_reproduction.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2105.08076/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 9 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: No author numerical source code or arrays were present in the arXiv archive.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![T001 main fig1c](outputs/figures/T001_main_fig1c.png)

![T002 main fig1d](outputs/figures/T002_main_fig1d.png)

![T003 main fig1e](outputs/figures/T003_main_fig1e.png)

![T004 main fig2a](outputs/figures/T004_main_fig2a.png)

![T005 main fig2b](outputs/figures/T005_main_fig2b.png)

![T006 main fig3a](outputs/figures/T006_main_fig3a.png)

![T007 main fig3b](outputs/figures/T007_main_fig3b.png)

![T008 supp fig1a](outputs/figures/T008_supp_fig1a.png)

![T009 supp fig1b](outputs/figures/T009_supp_fig1b.png)
