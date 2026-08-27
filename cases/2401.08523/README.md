# 2401.08523: Information and Majorization Theory for Fermionic Phase-Space Distributions

Preprint: [arXiv:2401.08523 — Information and Majorization Theory for Fermionic Phase-Space Distributions](https://arxiv.org/abs/2401.08523v2)

Published as: [Information and Majorization Theory for Fermionic Phase-Space Distributions](https://doi.org/10.1103/3qg7-r4mq)

Formal citation: 135, 110201 (2025) · DOI `10.1103/3qg7-r4mq` · Locator `110201`

Public status: **Partial scientific reproduction** · Audit score: **90.00/100**

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

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2401.08523/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: All two main figures and all four numerical panels are generated from the paper's closed-form equations. The supplement contains derivations but no additional figures. Original source figures are isolated to terminal pixel evaluation and are never numerical inputs.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![figure 1 fermi dirac](outputs/figures/figure_1_fermi_dirac.png)

![figure 2 uncertainty relations](outputs/figures/figure_2_uncertainty_relations.png)
