# 10.1103-PhysRevB.91.085420: Interband coherence induced correction to adiabatic pumping in periodically driven systems

Preprint: **No preprint recorded as of 2026-07-14**

Published as: [Interband coherence induced correction to adiabatic pumping in periodically driven systems](https://doi.org/10.1103/PhysRevB.91.085420)

Formal citation: Physical Review B 91, 085420 (2015) · DOI `10.1103/PhysRevB.91.085420` · Locator `085420`

Public status: **Scientific reproduction — visual review pending** · Audit score: **79.54/100**

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

### fig1 comparison comparison

![fig1 comparison paper reference versus independent reproduction](docs/comparisons/fig1_comparison.png)

### fig2 comparison comparison

![fig2 comparison paper reference versus independent reproduction](docs/comparisons/fig2_comparison.png)

### fig3 comparison comparison

![fig3 comparison paper reference versus independent reproduction](docs/comparisons/fig3_comparison.png)

### fig4 comparison comparison

![fig4 comparison paper reference versus independent reproduction](docs/comparisons/fig4_comparison.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/10.1103-PhysRevB.91.085420/code
python scripts/run_reproduction.py --config config/implementation_closure.json --output-root outputs/public_quick_run
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 4 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Remaining lifecycle boundaries: parameters=paper_exact, causal_resolution=not_required, pixel=missing, independent_review=missing, review_scope=missing, paper_assessment=missing.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig1 reproduction](outputs/figures/fig1_reproduction.png)

![fig2 overlay](outputs/figures/fig2_overlay.png)

![fig2 reproduction](outputs/figures/fig2_reproduction.png)

![fig3 reproduction](outputs/figures/fig3_reproduction.png)

![fig4 reproduction](outputs/figures/fig4_reproduction.png)
