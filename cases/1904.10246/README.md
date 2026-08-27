# 1904.10246: Amplitude estimation without phase estimation

Preprint: [arXiv:1904.10246v2 — Amplitude estimation without phase estimation](https://arxiv.org/abs/1904.10246v2)

Published as: [Amplitude estimation without phase estimation](https://doi.org/10.1007/s11128-019-2565-2)

Formal citation: 19, 75 (2020) · DOI `10.1007/s11128-019-2565-2` · Locator `75`

Public status: **Partial scientific reproduction** · Audit score: **93.75/100**

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
cd cases/1904.10246/code
python scripts/run_reproduction.py --target T_FIG2 --config config/implementation.json --smoke
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Raw inputs frozen for baseline-fast-2026-07-29; keep case in mapping_pending until its isolated trial starts.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig2 query error](outputs/figures/fig2_query_error.png)

![figa percentile comparison](outputs/figures/figa_percentile_comparison.png)

![table1 complexities](outputs/figures/table1_complexities.png)

![table2 resources](outputs/figures/table2_resources.png)
