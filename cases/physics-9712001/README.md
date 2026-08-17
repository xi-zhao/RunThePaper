# physics-9712001: Real Spectra in Non-Hermitian Hamiltonians Having PT Symmetry

Preprint: [physics/9712001v3 — Real Spectra in Non-Hermitian Hamiltonians Having PT Symmetry](https://arxiv.org/abs/physics/9712001)

Published as: [Real Spectra in Non-Hermitian Hamiltonians Having PT Symmetry](https://doi.org/10.1103/PhysRevLett.80.5243)

Formal citation: 80, 5243-5246 (1998) · DOI `10.1103/PhysRevLett.80.5243` · Locator `5243-5246`

Public status: **Scientific reproduction — paper-error candidates identified** · Audit score: **92.19/100**

All seven numerical targets have paper-scale code; formal isolated execution and independent review remain.

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

## Paper Reference vs Independent Reproduction

Each board contains only the minimum paper excerpt needed for validation and places it beside an independently generated result. Visual agreement is a scientific-region diagnostic, not author-data-level equivalence.

### main fig1 comparison comparison

![main fig1 comparison paper reference versus independent reproduction](docs/comparisons/main_fig1_comparison.png)

### main fig1 pixel board comparison

![main fig1 pixel board paper reference versus independent reproduction](docs/comparisons/main_fig1_pixel_board.png)

### main fig3 comparison comparison

![main fig3 comparison paper reference versus independent reproduction](docs/comparisons/main_fig3_comparison.png)

### main fig3 pixel board comparison

![main fig3 pixel board paper reference versus independent reproduction](docs/comparisons/main_fig3_pixel_board.png)

### table i comparison comparison

![table i comparison paper reference versus independent reproduction](docs/comparisons/table_i_comparison.png)

### table ii comparison comparison

![table ii comparison paper reference versus independent reproduction](docs/comparisons/table_ii_comparison.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/physics-9712001/code
python scripts/run_reproduction.py --config config/smoke.json --output-root outputs/public_quick_run
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 6 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, parameters=paper_exact, causal_resolution=terminal_blocker, science=pending, pixel=passed_with_not_comparable, review_scope=incomplete, paper_assessment=paper_error_candidate.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![main fig1 reproduction](outputs/figures/main_fig1_reproduction.png)

![main fig3 reproduction](outputs/figures/main_fig3_reproduction.png)

![table i reproduction](outputs/figures/table_i_reproduction.png)

![table ii reproduction](outputs/figures/table_ii_reproduction.png)
