# 1804.04672: Non-Hermitian Chern bands

Preprint: [arXiv:1804.04672 — Non-Hermitian Chern bands](https://arxiv.org/abs/1804.04672)

Published as: [Non-Hermitian Chern Bands](https://doi.org/10.1103/PhysRevLett.121.136802)

Formal citation: Physical Review Letters 121, 136802 (2018) · DOI `10.1103/PhysRevLett.121.136802` · Locator `136802`

Public status: **Partial scientific reproduction** · Audit score: **86.22/100**

Author scientific closure v1 executes all seven formerly pending targets: six have passing attested scientific checks and T012 has a direct publication-input audit plus representative witness. No independent paper verdict is authored.

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
cd cases/1804.04672/code
python scripts/run_reproduction.py --config config/implementation_closure.json --output outputs/public_quick_run
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, parameters=mixed, parameter_provenance=missing, causal_resolution=repair_required, science=pending, execution=failed, pixel=missing, independent_review=missing, review_scope=missing, paper_assessment=missing.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![edge branch diagnostic](outputs/figures/edge_branch_diagnostic.png)

![fig1 open boundary phase](outputs/figures/fig1_open_boundary_phase.png)

![fig1 reference comparison](outputs/figures/fig1_reference_comparison.png)

![fig2 reference comparison](outputs/figures/fig2_reference_comparison.png)

![fig2 square dynamics](outputs/figures/fig2_square_dynamics.png)

![fig3a cylinder phase](outputs/figures/fig3a_cylinder_phase.png)

![fig3a reference comparison](outputs/figures/fig3a_reference_comparison.png)

![fig3b reference comparison](outputs/figures/fig3b_reference_comparison.png)

![figs2 gap scaling](outputs/figures/figs2_gap_scaling.png)

![figs2 reference comparison](outputs/figures/figs2_reference_comparison.png)

![figs3 disk phase](outputs/figures/figs3_disk_phase.png)

![figs3 reference comparison](outputs/figures/figs3_reference_comparison.png)

![first target](outputs/figures/first_target.png)

![supplement s4](outputs/figures/supplemental_smoke_v2/supplement_s4.png)

![supplement s5](outputs/figures/supplemental_smoke_v2/supplement_s5.png)

![supplement s6](outputs/figures/supplemental_smoke_v2/supplement_s6.png)

![supplement s8](outputs/figures/supplemental_smoke_v2/supplement_s8.png)

![supplement s9](outputs/figures/supplemental_smoke_v2/supplement_s9.png)
