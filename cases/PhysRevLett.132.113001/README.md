# PhysRevLett.132.113001: Precision-Spectroscopic Determination of the Binding Energy of a Two-Body Quantum System: The Hydrogen Atom and the Proton-Size Puzzle

Preprint: **No preprint recorded as of 2026-08-11**

Published as: [Precision-Spectroscopic Determination of the Binding Energy of a Two-Body Quantum System: The Hydrogen Atom and the Proton-Size Puzzle](https://doi.org/10.1103/PhysRevLett.132.113001)

Formal citation: Phys. Rev. Lett. 132, 113001 (2024) · DOI `10.1103/PhysRevLett.132.113001` · Locator `113001`

Public status: **Partial scientific reproduction** · Audit score: **39.29/100**

The known source lower bound contains 9 eligible theory-numerical items: 5 partial/data-backed and 4 explicitly uncovered; the unavailable formal Supplement leaves an unknown remainder.

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

### T001 source vs reproduction comparison

![T001 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T001_source_vs_reproduction.png)

### T002 source vs reproduction comparison

![T002 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T002_source_vs_reproduction.png)

### T003 source vs reproduction comparison

![T003 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T003_source_vs_reproduction.png)

### T004 source vs reproduction comparison

![T004 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T004_source_vs_reproduction.png)

### T005 source vs reproduction comparison

![T005 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T005_source_vs_reproduction.png)

### T006 source vs reproduction comparison

![T006 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T006_source_vs_reproduction.png)

### T007 source vs reproduction comparison

![T007 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T007_source_vs_reproduction.png)

### T008 source vs reproduction comparison

![T008 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T008_source_vs_reproduction.png)

### T009 source vs reproduction comparison

![T009 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T009_source_vs_reproduction.png)

### T010 source vs reproduction comparison

![T010 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T010_source_vs_reproduction.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/PhysRevLett.132.113001/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 10 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, parameters=mixed, parameter_provenance=failed, causal_resolution=repair_required, science=pending, pixel=missing, independent_review=missing, review_scope=missing, paper_assessment=missing.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![T001 fig1 n20 stark](outputs/figures/feature/T001_fig1_n20_stark.png)

![T002 fig1 n24 stark](outputs/figures/feature/T002_fig1_n24_stark.png)

![T003 fig3 theory](outputs/figures/feature/T003_fig3_theory.png)

![T004 fig4 metrology](outputs/figures/feature/T004_fig4_metrology.png)

![T005 fig5b stark model](outputs/figures/feature/T005_fig5b_stark_model.png)

![T006 fig5c doppler model](outputs/figures/feature/T006_fig5c_doppler_model.png)

![T007 table1 uncertainties](outputs/figures/feature/T007_table1_uncertainties.png)

![T008 table2 rydberg](outputs/figures/feature/T008_table2_rydberg.png)

![T009 supp field free](outputs/figures/feature/T009_supp_field_free.png)

![T010 supp stark table](outputs/figures/feature/T010_supp_stark_table.png)
