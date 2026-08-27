# 2608.03987: Realified tensor networks: quantum circuit simulation on real-valued matrix accelerators

Preprint: [arXiv:2608.03987 — Realified tensor networks: quantum circuit simulation on real-valued matrix accelerators](https://arxiv.org/abs/2608.03987)

Formal publication: **Not recorded as of 2026-08-07**

Public status: **Partial scientific reproduction** · Audit score: **72.00/100**

Figure 8 passes independently at full scale; Figure 9 is fully computed but its paper-threshold feature differs on nine additional circuits.

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
cd cases/2608.03987/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Author Rust code and contraction plans are excluded from primary evidence. Figure 8 passed; Figure 9 produced 57/67 circuits below the paper threshold versus 66/67 in the source.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig8 cost law](outputs/figures/fig8_cost_law.png)

![fig9 pipeline](outputs/figures/fig9_pipeline.png)
