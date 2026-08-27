# 1711.03528: Quantum many-body scars

Preprint: [arXiv:1711.03528 — Quantum many-body scars](https://arxiv.org/abs/1711.03528)

Published as: [Weak ergodicity breaking from quantum many-body scars](https://doi.org/10.1038/s41567-018-0137-5)

Formal citation: Nature Physics 14, 745–749 (2018) · DOI `10.1038/s41567-018-0137-5` · Locator `745–749`

Public status: **Partial scientific reproduction** · Audit score: **72.50/100**

量子多体 scar 的核心数值特征和 L=28 同一对称 sector 已复现；L=32 与 bond-400 MPS 路径已有代码，但尚未执行论文尺度收敛网格。

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
cd cases/1711.03528/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: The paper-scale L=32 symmetry-resolved exact diagonalization and thermodynamic-limit iTEBD are not rerun locally.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig1 hilbert graph reproduction](outputs/figures/fig1_hilbert_graph_reproduction.png)

![fig2 special states reproduction](outputs/figures/fig2_special_states_reproduction.png)

![fig4 level statistics reproduction](outputs/figures/fig4_level_statistics_reproduction.png)

![fig ent dynamics reproduction](outputs/figures/fig_ent_dynamics_reproduction.png)

![sector level statistics](outputs/figures/sector_level_statistics.png)

![sector scar tower](outputs/figures/sector_scar_tower.png)
