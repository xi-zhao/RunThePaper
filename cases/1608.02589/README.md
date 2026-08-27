# 1608.02589: Discrete time crystals: rigidity, criticality, and realizations

Preprint: [arXiv:1608.02589 — Discrete time crystals: rigidity, criticality, and realizations](https://arxiv.org/abs/1608.02589)

Published as: [Discrete Time Crystals: Rigidity, Criticality, and Realizations](https://doi.org/10.1103/PhysRevLett.118.030401)

Formal citation: Phys. Rev. Lett. 118, 030401 (2017) · DOI `10.1103/PhysRevLett.118.030401` · Locator `030401`

Public status: **Partial scientific reproduction** · Audit score: **73.56/100**

Existing frozen evidence covers 32 of 89 eligible atomic reproduction items. Fifty-seven uncovered items are now explicit zero-credit targets with direct/root cause, code-fault status, and next discriminating tests.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Equation-level derivation](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Public evidence index](docs/EVIDENCE_INDEX.md)
- [Comparison policy](docs/COMPARISON_POLICY.md)
- [Scientific consistency report](docs/CONSISTENCY_REPORT.md)
- [Paper review protocol](docs/PAPER_REVIEW_PROTOCOL_V2.md)
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
cd cases/1608.02589/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Second iteration reproduces core DTC rigidity features at L=14. Corrected endpoint mutual information reproduces the main finite-size-flow feature. Full phase diagram, scaling collapse, and critical exponents remain large-scale ED targets.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig1 subharmonic rigidity reproduction](outputs/figures/fig1_subharmonic_rigidity_reproduction.png)

![fig2 level statistics variance reproduction](outputs/figures/fig2_level_statistics_variance_reproduction.png)

![fig3 mutual information proxy reproduction](outputs/figures/fig3_mutual_information_proxy_reproduction.png)

![fig3 scaling collapse](outputs/figures/fig3_scaling_collapse.png)

![fig4 long range variance reproduction](outputs/figures/fig4_long_range_variance_reproduction.png)

![iteration2 fig1 L14 subharmonic rigidity](outputs/figures/iteration2_fig1_L14_subharmonic_rigidity.png)

![iteration2 fig1 phase boundary proxy](outputs/figures/iteration2_fig1_phase_boundary_proxy.png)

![iteration2 fig2 level statistics variance L10](outputs/figures/iteration2_fig2_level_statistics_variance_L10.png)

![iteration2 fig3 mutual information corrected](outputs/figures/iteration2_fig3_mutual_information_corrected.png)

![iteration2 fig4 long range variance L10](outputs/figures/iteration2_fig4_long_range_variance_L10.png)

![main fig1](outputs/figures/paper_scale_smoke/main_fig1.png)

![main fig2](outputs/figures/paper_scale_smoke/main_fig2.png)

![main fig3](outputs/figures/paper_scale_smoke/main_fig3.png)

![main fig4](outputs/figures/paper_scale_smoke/main_fig4.png)

![supp fig s1](outputs/figures/paper_scale_smoke/supp_fig_s1.png)

![supp fig s2](outputs/figures/paper_scale_smoke/supp_fig_s2.png)

![supp fig s3](outputs/figures/paper_scale_smoke/supp_fig_s3.png)
