# 2610.10731: Single-shot magic state factories for quantum LDPC codes

Preprint: [arXiv:2610.10731v1 — Single-shot magic state factories for quantum LDPC codes](https://arxiv.org/abs/2610.10731v1)

Formal publication: **Not recorded as of 2026-10-13**

Public status: **Partial scientific reproduction** · Audit score: **Not assessed / 未评分**

Full SD6 preparation decoding improves acceptance, with a remaining quantitative gap. 完整噪声下的制备译码缩小了接受率差距；完整条件逻辑错误率和资源优势仍待复现。

![Independently generated overview](outputs/figures/acceptance-generated.png)

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
| Fig. 5(b) | Full SD6 preparation decoding improves acceptance, with a remaining quantitative gap. 完整噪声下的制备译码缩小了接受率差距；完整条件逻辑错误率和资源优势仍待复现。 | [PNG](outputs/figures/acceptance-generated.png) | [JSON](outputs/checks/preparation-summary.json) |

## Paper Reference vs Independent Reproduction

Minimal validation comparison with arXiv:2610.10731v1. Reference marks/excerpts and independently computed curves are labeled separately. Reference content is excluded from the repository content license. Visual or read-point agreement does not establish author-data-level equivalence.

### Latest bounded comparison comparison

![Latest bounded comparison paper reference versus independent reproduction](docs/comparisons/preparation-acceptance.png)

### Fig. 5(b): Full SD6 preparation decoding improves acceptance, with a remaining quantitative gap. 完整噪声下的制备译码缩小了接受率差距；完整条件逻辑错误率和资源优势仍待复现。

![Fig. 5(b) reproduction](outputs/figures/acceptance-generated.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2610.10731/code/requirements.txt
cd cases/2610.10731/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 1 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Partial reproduction. Exact finite-circuit acceptance is not complete logical magic-state fidelity; equal author circuit/decoder conventions and low-error-rate resource curves remain unresolved.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
