# PhysRevA.47.5138: Squeezed Spin States

Preprint: **No preprint recorded as of 2026-08-17**

Published as: [Squeezed Spin States](https://doi.org/10.1103/PhysRevA.47.5138)

Formal citation: 47, 5138-5143 (1993) · DOI `10.1103/PhysRevA.47.5138` · Locator `5138-5143`

Public status: **Scientific reproduction — independent review pending** · Audit score: **87.34/100**

All seven numerical panels are independently reproduced; fresh-context review remains.

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

### main fig2 comparison comparison

![main fig2 comparison paper reference versus independent reproduction](docs/comparisons/main_fig2_comparison.png)

### main fig3 comparison comparison

![main fig3 comparison paper reference versus independent reproduction](docs/comparisons/main_fig3_comparison.png)

### main fig4 comparison comparison

![main fig4 comparison paper reference versus independent reproduction](docs/comparisons/main_fig4_comparison.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/PhysRevA.47.5138/code
python scripts/run_reproduction.py --config config/smoke.json
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 3 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Remaining lifecycle boundaries: parameters=paper_exact, causal_resolution=not_required, independent_review=stale, review_scope=stale, paper_assessment=stale.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![main fig2 reproduction](outputs/figures/main_fig2_reproduction.png)

![main fig3 reproduction](outputs/figures/main_fig3_reproduction.png)

![main fig4 reproduction](outputs/figures/main_fig4_reproduction.png)
