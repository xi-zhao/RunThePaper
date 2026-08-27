# 2607.15070: Casimir effect for a massive scalar field confined between parallel plates with a spatially varying effective mass

Preprint: [arXiv:2607.15070v1 — Casimir effect for a massive scalar field confined between parallel plates with a spatially varying effective mass](https://arxiv.org/abs/2607.15070v1)

Formal publication: **Not recorded as of 2026-07-29**

Public status: **Scientific reproduction — independent review pending** · Audit score: **90.00/100**

Case scaffolded from framework/templates/paper_case.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Equation-level derivation](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Public evidence index](docs/EVIDENCE_INDEX.md)
- [Comparison policy](docs/COMPARISON_POLICY.md)
- [Scientific consistency report](docs/CONSISTENCY_REPORT.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Paper Reference vs Independent Reproduction

Each board contains only the minimum paper excerpt needed for validation and places it beside an independently generated result. Visual agreement is a scientific-region diagnostic, not author-data-level equivalence.

### fig2 left comparison comparison

![fig2 left comparison paper reference versus independent reproduction](docs/comparisons/fig2_left_comparison.png)

### fig2 right comparison comparison

![fig2 right comparison paper reference versus independent reproduction](docs/comparisons/fig2_right_comparison.png)

### fig3 comparison comparison

![fig3 comparison paper reference versus independent reproduction](docs/comparisons/fig3_comparison.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2607.15070/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 3 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Raw inputs frozen for baseline-fast-2026-07-29; keep case in mapping_pending until its isolated trial starts.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig2 left](outputs/figures/fig2_left.png)

![fig2 right](outputs/figures/fig2_right.png)

![fig3 ratio](outputs/figures/fig3_ratio.png)
