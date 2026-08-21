# quant-ph-0507004: Large-N Scaling Behavior of the Lipkin-Meshkov-Glick Model

Preprint: [arXiv:quant-ph/0507004 — Large-N Scaling Behavior of the Lipkin-Meshkov-Glick Model](https://arxiv.org/abs/quant-ph/0507004)

Published as: [Large-N Scaling Behavior of the Lipkin-Meshkov-Glick Model](https://doi.org/10.1103/PhysRevLett.95.050402)

Formal citation: Phys. Rev. Lett. 95, 050402 (2005) · DOI `10.1103/PhysRevLett.95.050402` · Locator `050402`

Public status: **Scientific reproduction — paper-error candidates identified** · Audit score: **69.00/100**

Whole-paper exact parity-block implementation; Main Fig. 1 finite-N discrepancy retained for fresh review.

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
cd cases/quant-ph-0507004/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, parameters=mixed, causal_resolution=repair_required, science=failed, pixel=not_comparable, paper_assessment=mixed.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![main fig1 spacing scaling](outputs/figures/main_fig1_spacing_scaling.png)

![main fig2 critical spectrum](outputs/figures/main_fig2_critical_spectrum.png)
