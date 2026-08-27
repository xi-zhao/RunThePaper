# 1508.03344: Phase Structure of Driven Quantum Systems

Preprint: [arXiv:1508.03344 — Phase Structure of Driven Quantum Systems](https://arxiv.org/abs/1508.03344)

Published as: [Phase Structure of Driven Quantum Systems](https://doi.org/10.1103/PhysRevLett.116.250401)

Formal citation: 116, 250401 (2016) · DOI `10.1103/PhysRevLett.116.250401` · Locator `250401`

Public status: **Partial scientific reproduction** · Audit score: **72.86/100**

Case scaffolded from framework/templates/paper_case.

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

### T001 comparison comparison

![T001 comparison paper reference versus independent reproduction](docs/comparisons/T001_comparison.png)

### T002 comparison comparison

![T002 comparison paper reference versus independent reproduction](docs/comparisons/T002_comparison.png)

### T003 comparison comparison

![T003 comparison paper reference versus independent reproduction](docs/comparisons/T003_comparison.png)

### T004 comparison comparison

![T004 comparison paper reference versus independent reproduction](docs/comparisons/T004_comparison.png)

### T005 comparison comparison

![T005 comparison paper reference versus independent reproduction](docs/comparisons/T005_comparison.png)

### T006 comparison comparison

![T006 comparison paper reference versus independent reproduction](docs/comparisons/T006_comparison.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1508.03344/code
python scripts/run_reproduction.py --config config/reduced_all_targets.json
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 6 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: The arXiv archive contains manuscript TeX and vector figures only; no author computational code or numeric arrays were accessed.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![main fig1 reproduction](outputs/figures/main_fig1_reproduction.png)

![main fig2 reproduction](outputs/figures/main_fig2_reproduction.png)
