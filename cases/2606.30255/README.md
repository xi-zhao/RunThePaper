# 2606.30255: Photonic Violation of Wigner's Inequality

Preprint: [arXiv:2606.30255v1 — Photonic Violation of Wigner's Inequality](https://arxiv.org/abs/2606.30255v1)

Formal publication: **Not recorded as of 2026-07-30**

Public status: **Scientific reproduction — independent review pending** · Audit score: **97.50/100**

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

### fig003 theory comparison comparison

![fig003 theory comparison paper reference versus independent reproduction](docs/comparisons/fig003_theory_comparison.png)

### fig004 theory comparison comparison

![fig004 theory comparison paper reference versus independent reproduction](docs/comparisons/fig004_theory_comparison.png)

### fig005a theory comparison comparison

![fig005a theory comparison paper reference versus independent reproduction](docs/comparisons/fig005a_theory_comparison.png)

### fig005b theory comparison comparison

![fig005b theory comparison paper reference versus independent reproduction](docs/comparisons/fig005b_theory_comparison.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2606.30255/code
python scripts/run_reproduction.py --config config/implementation_smoke.json --output-root outputs/public_quick_run
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 4 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, parameters=paper_exact, causal_resolution=not_required, independent_review=missing, review_scope=missing, paper_assessment=missing.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig003 theory](outputs/figures/fig003_theory.png)

![fig004 theory](outputs/figures/fig004_theory.png)

![fig005a theory](outputs/figures/fig005a_theory.png)

![fig005b theory](outputs/figures/fig005b_theory.png)
