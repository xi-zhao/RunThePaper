# 2607.08212: Möbius-Guided Diagonal-Gate Compilation with Native Multiqubit Controlled-Phase Gates on Neutral-Atom Processors

Preprint: [arXiv:2607.08212 — Möbius-Guided Diagonal-Gate Compilation with Native Multiqubit Controlled-Phase Gates on Neutral-Atom Processors](https://arxiv.org/abs/2607.08212)

Formal publication: **Not recorded as of 2026-08-04**

Public status: **Partial scientific reproduction** · Audit score: **70.85/100**

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
cd cases/2607.08212/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Bounded pass reproduces the algebra and Fig. 3 gate accounting; routed benchmark metadata remains incomplete. User-approved proxy campaign expanded on 2026-07-10 to every locally feasible target: Figs. 4/5/8 eight-family matrix, Fig. 6 scaling, and Fig. 7 sensitivity. The Fig. 7 proxy preserves a genuine mismatch: no paper-like break-even contours appear within the declared 0-20% grid. Exact Figs. 4-8 remain blocked by author generators, route state, timing environment, and ZX configuration.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig3 gate accounting reproduction](outputs/figures/fig3_gate_accounting_reproduction.png)

![proxy duration compile scaling](outputs/figures/proxy_duration_compile_scaling.png)

![proxy fidelity all families](outputs/figures/proxy_fidelity_all_families.png)

![proxy moves all families](outputs/figures/proxy_moves_all_families.png)

![proxy native error sensitivity](outputs/figures/proxy_native_error_sensitivity.png)

![proxy routing mechanism](outputs/figures/proxy_routing_mechanism.png)

![proxy stages all families](outputs/figures/proxy_stages_all_families.png)
