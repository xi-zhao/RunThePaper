# cond-mat-0411737: Quantum Spin Hall Effect in Graphene

Preprint: [arXiv:cond-mat/0411737 — Quantum Spin Hall Effect in Graphene](https://arxiv.org/abs/cond-mat/0411737)

Published as: [Quantum Spin Hall Effect in Graphene](https://doi.org/10.1103/PhysRevLett.95.226801)

Formal citation: 95, 226801 (2005) · DOI `10.1103/PhysRevLett.95.226801` · Locator `226801`

Public status: **Partial scientific reproduction** · Audit score: **89.00/100**

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

### main fig1 comparison comparison

![main fig1 comparison paper reference versus independent reproduction](docs/comparisons/main_fig1_comparison.png)

### main fig1 scientific region comparison comparison

![main fig1 scientific region comparison paper reference versus independent reproduction](docs/comparisons/main_fig1_scientific_region_comparison.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/cond-mat-0411737/code
python scripts/run_reproduction.py --config config/paper_reconstructed.json --output-root outputs/public_quick_run
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 2 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Full PDF and source inventory audited; one numerical figure target (T001). Author source archive contains manuscript TeX and rendered EPS only, with no computational code or numeric arrays. Clean-room zigzag ribbon solver and paper-scale local run contract implemented; formal isolated run pending.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![main fig1 reproduction](outputs/figures/main_fig1_reproduction.png)
