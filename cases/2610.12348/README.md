# 2610.12348: Constructing Large and Structured Decoherence-Free Subspaces in Hybrid Quantum Systems

Preprint: [arXiv:2610.12348v1 — Constructing Large and Structured Decoherence-Free Subspaces in Hybrid Quantum Systems](https://arxiv.org/abs/2610.12348v1)

Formal publication: **Not recorded as of 2026-10-13**

Public status: **Partial scientific reproduction** · Audit score: **Not assessed / 未评分**

Structured dark-state calculations and bounded dynamics checks, with a tested normalization explanation for H3. 暗态结构与有限动力学核验已有结果；H3 归一化解释获多初态支持，大样本及截断验证尚未完成。

![Independently generated overview](outputs/figures/h3-generated.png)

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Evidence map / 证据索引](docs/EVIDENCE_INDEX.md)
- [Differences and remaining work / 差异与待办](docs/BOUNDARIES.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Main Reproduced Results

| Paper item | Reproduced result | Figure | Check |
| --- | --- | --- | --- |
| Fig. H3 | Structured dark-state calculations and bounded dynamics checks, with a tested normalization explanation for H3. 暗态结构与有限动力学核验已有结果；H3 归一化解释获多初态支持，大样本及截断验证尚未完成。 | [PNG](outputs/figures/h3-generated.png) | [JSON](outputs/checks/h3-summary.json) |

## Paper Reference vs Independent Reproduction

Minimal validation comparison with arXiv:2610.12348v1. Reference marks/excerpts and independently computed curves are labeled separately. Reference content is excluded from the repository content license. Visual or read-point agreement does not establish author-data-level equivalence.

### Latest bounded comparison comparison

![Latest bounded comparison paper reference versus independent reproduction](docs/comparisons/h3-normalization.png)

### Fig. H3: Structured dark-state calculations and bounded dynamics checks, with a tested normalization explanation for H3. 暗态结构与有限动力学核验已有结果；H3 归一化解释获多初态支持，大样本及截断验证尚未完成。

![Fig. H3 reproduction](outputs/figures/h3-generated.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2610.12348/code/requirements.txt
cd cases/2610.12348/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 1 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Partial reproduction. Raw trajectory entropy is a normalization diagnostic, not physical von Neumann entropy. H3 large-ensemble/cutoff verification, remaining source figures and source-convention ambiguities remain open.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
