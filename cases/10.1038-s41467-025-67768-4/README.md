# 10.1038-s41467-025-67768-4: Demonstrating quantum error mitigation on logical qubits

Preprint: [arXiv:2501.09079 — Demonstrating quantum error mitigation on logical qubits](https://www.nature.com/articles/s41467-025-67768-4)

Published as: [Demonstrating quantum error mitigation on logical qubits](https://doi.org/10.1038/s41467-025-67768-4)

Formal citation: Nature Communications 17, 1021 (2026) · DOI `10.1038/s41467-025-67768-4` · Locator `1021`

Public status: **Partial scientific reproduction** · Audit score: **72.25/100**

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

## Paper Reference vs Independent Reproduction

Each board contains only the minimum paper excerpt needed for validation and places it beside an independently generated result. Visual agreement is a scientific-region diagnostic, not author-data-level equivalence.

### T001 main fig2c source vs reproduction comparison

![T001 main fig2c source vs reproduction paper reference versus independent reproduction](docs/comparisons/T001_main_fig2c_source_vs_reproduction.png)

### T002 main fig3c source vs reproduction comparison

![T002 main fig3c source vs reproduction paper reference versus independent reproduction](docs/comparisons/T002_main_fig3c_source_vs_reproduction.png)

### T002 supp fig4 source vs reproduction comparison

![T002 supp fig4 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T002_supp_fig4_source_vs_reproduction.png)

### T003 main fig3e source vs reproduction comparison

![T003 main fig3e source vs reproduction paper reference versus independent reproduction](docs/comparisons/T003_main_fig3e_source_vs_reproduction.png)

### T004 main fig4b source vs reproduction comparison

![T004 main fig4b source vs reproduction paper reference versus independent reproduction](docs/comparisons/T004_main_fig4b_source_vs_reproduction.png)

### T004 main fig4c source vs reproduction comparison

![T004 main fig4c source vs reproduction paper reference versus independent reproduction](docs/comparisons/T004_main_fig4c_source_vs_reproduction.png)

### T004 supp fig7ace source vs reproduction comparison

![T004 supp fig7ace source vs reproduction paper reference versus independent reproduction](docs/comparisons/T004_supp_fig7ace_source_vs_reproduction.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/10.1038-s41467-025-67768-4/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 7 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, numerical_scope=incomplete, parameters=mixed, parameter_provenance=missing, causal_resolution=repair_required, science=pending, pixel=missing, independent_review=missing, review_scope=missing, paper_assessment=missing.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![main fig2c feedback](outputs/figures/main_fig2c_feedback.png)

![main fig3c repetition](outputs/figures/main_fig3c_repetition.png)

![main fig3e repetition](outputs/figures/main_fig3e_repetition.png)

![main fig4b bloch](outputs/figures/main_fig4b_bloch.png)

![main fig4c surface](outputs/figures/main_fig4c_surface.png)

![supp fig4 repetition](outputs/figures/supp_fig4_repetition.png)

![supp fig7ace surface](outputs/figures/supp_fig7ace_surface.png)

![supp fig8 complete zne](outputs/figures/supp_fig8_complete_zne.png)

![supp fig9 logical memory](outputs/figures/supp_fig9_logical_memory.png)

![supp table3 fixed error](outputs/figures/supp_table3_fixed_error.png)
