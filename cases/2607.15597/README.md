# 2607.15597: Deterministic atom-shuttle interconnects via ultrafast atom-ion entangling gate

Preprint: [arXiv:2607.15597 — Deterministic atom-shuttle interconnects via ultrafast atom-ion entangling gate](https://arxiv.org/abs/2607.15597)

Formal publication: **Not recorded as of 2026-07-22**

Public status: **Partial scientific reproduction** · Audit score: **81.85/100**

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
cd cases/2607.15597/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Local feature reproduction scored 75.21/100; exact author-run equivalence remains blocked by missing MQDT, qLDPC, and open-system inputs.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig2 reproduction](outputs/figures/fig2_reproduction.png)

![fig3 reproduction](outputs/figures/fig3_reproduction.png)

![fig4 reproduction](outputs/figures/fig4_reproduction.png)

![figs1 closure reproduction](outputs/figures/figs1_closure_reproduction.png)

![figs3 thermal reproduction](outputs/figures/figs3_thermal_reproduction.png)

![figs5 qldpc projection reproduction](outputs/figures/figs5_qldpc_projection_reproduction.png)

![figs6 circular dynamics reproduction](outputs/figures/figs6_circular_dynamics_reproduction.png)

![figs7 circular thermal reproduction](outputs/figures/figs7_circular_thermal_reproduction.png)
