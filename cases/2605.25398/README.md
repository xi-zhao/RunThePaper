# 2605.25398: Boson Sampling as a Probe of Chaotic and Integrable Quantum Dynamics

Preprint: [arXiv:2605.25398 — Boson Sampling as a Probe of Chaotic and Integrable Quantum Dynamics in a Photonic Chip](https://arxiv.org/abs/2605.25398)

Formal publication: **Not recorded as of 2026-07-14**

Public status: **Scientific reproduction — visual review pending** · Audit score: **85.30/100**

Seven numerical targets and all 20 eligible numerical items are backed by a clean-room isolated run. The even M=4,6,...,22 scaling grid, the paper's 2000-instance ideal Fig. 3/Fig. 4/Fig. S5 curves, all collision-free OTOCs including the initial state, and the t=300..1000 FFT test pass without author code, author arrays, or source pixels as inputs.

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
cd cases/2605.25398/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Remaining lifecycle boundaries: parameters=paper_exact, causal_resolution=not_required, pixel=missing, independent_review=stale, review_scope=stale, paper_assessment=stale.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig2 output distribution reproduction](outputs/figures/fig2_output_distribution_reproduction.png)

![fig3 main probes reproduction](outputs/figures/fig3_main_probes_reproduction.png)

![fig4 otoc pr reproduction](outputs/figures/fig4_otoc_pr_reproduction.png)

![figS1 conditional probability reproduction](outputs/figures/figS1_conditional_probability_reproduction.png)

![figS4 scaling reproduction](outputs/figures/figS4_scaling_reproduction.png)

![figS5 ideal otocs reproduction](outputs/figures/figS5_ideal_otocs_reproduction.png)

![figS6 extra otoc reproduction](outputs/figures/figS6_extra_otoc_reproduction.png)
