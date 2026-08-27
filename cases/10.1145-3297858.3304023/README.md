# 10.1145-3297858.3304023: Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices

Preprint: [arXiv:1809.02573 — Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices](https://arxiv.org/abs/1809.02573)

Published as: [Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices](https://doi.org/10.1145/3297858.3304023)

Formal citation: ASPLOS '19, pp. 1001–1014 · DOI `10.1145/3297858.3304023` · Locator `1001–1014`

Public status: **Partial scientific reproduction** · Audit score: **68.29/100**

SABRE 的核心算法机制已经复现，小例子可以精确对齐；但 Table II 是论文里最重要的数值表，目前只达到部分一致。

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
cd cases/10.1145-3297858.3304023/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Remaining lifecycle boundaries: parameters=mixed, parameter_provenance=failed, causal_resolution=terminal_blocker, execution=missing, pixel=missing, independent_review=missing, review_scope=missing, paper_assessment=missing.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![core benchmarks qft](outputs/figures/core_benchmarks_qft.png)

![decay tradeoff](outputs/figures/decay_tradeoff.png)

![paper swap example trace](outputs/figures/paper_swap_example_trace.png)

![table2 gop comparison](outputs/figures/table2_gop_comparison.png)
