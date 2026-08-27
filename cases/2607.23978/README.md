# 2607.23978: Non-Hermitian-enhanced quantum sensing in an optical interferometer

Preprint: [arXiv:2607.23978 — Non-Hermitian-enhanced quantum sensing in an optical interferometer](https://arxiv.org/abs/2607.23978)

Formal publication: **Not recorded as of 2026-08-03**

Public status: **Partial scientific reproduction** · Audit score: **86.58/100**

Case scaffolded from framework/templates/paper_case.

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

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2607.23978/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Remaining lifecycle boundaries: numerical_scope=incomplete, parameters=mixed, causal_resolution=repair_required, science=pending, pixel=missing, paper_assessment=inconclusive.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig2 expectations](outputs/figures/fig2_expectations.png)

![fig2 optimal](outputs/figures/fig2_optimal.png)

![fig2 optimal pixel registered](outputs/figures/fig2_optimal_pixel_registered.png)

![fig3a](outputs/figures/fig3a.png)

![fig3a ordering audit](outputs/figures/fig3a_ordering_audit.png)

![fig3a pixel registered](outputs/figures/fig3a_pixel_registered.png)

![fig3bc](outputs/figures/fig3bc.png)

![fig3bc pixel registered](outputs/figures/fig3bc_pixel_registered.png)
