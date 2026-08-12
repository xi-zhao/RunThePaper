# 2512.23799: Efficient simulation of logical magic state preparation protocols

Preprint: [arXiv:2512.23799 — Efficient simulation of logical magic state preparation protocols](https://arxiv.org/abs/2512.23799)

Published as: [Efficient Simulation of Logical Magic State Preparation Protocols](https://doi.org/10.1103/fby6-xjbm)

Formal citation: PRX Quantum 7, 020329 (2026) · DOI `10.1103/fby6-xjbm` · Locator `020329`

Public status: **Partial scientific reproduction** · Audit score: **73.00/100**

Reconstructs the exact Steane [[7,1,3]] logical-H circuit and evaluates acceptance, logical infidelity, runtime, and sampling precision.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Paper Reference vs Independent Reproduction

The left column in each panel is a limited excerpt from Surti, Daguerre, and Kim, [PRX Quantum 7, 020329 (2026)](https://doi.org/10.1103/fby6-xjbm); the right column is generated independently from this case. These comparisons validate physical structure and key numerical features, not author-data-level or point-for-point equivalence.

### Fig. 1 (logical infidelity) comparison

![Fig. 1 (logical infidelity) paper reference versus independent reproduction](docs/comparisons/fig1_infidelity_comparison.png)

### Fig. 2 (acceptance rate) comparison

![Fig. 2 (acceptance rate) paper reference versus independent reproduction](docs/comparisons/fig2_acceptance_comparison.png)

### Fig. 3 (runtime) comparison

![Fig. 3 (runtime) paper reference versus independent reproduction](docs/comparisons/fig3_runtime_comparison.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2512.23799/code
python scripts/run_reproduction.py
python scripts/plot_reproduction.py
python scripts/run_steane_exact_benchmark.py --profile smoke
python scripts/plot_steane_exact_comparison.py
```

### Full paper-scale rerun

The paper profile evaluates all 12 physical-error points with the larger Monte Carlo shot budget used by the published case output.

```bash
cd cases/2512.23799/code
python scripts/run_steane_exact_benchmark.py --profile paper
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 3 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Exact-circuit acceptance matches all 12 validated points, while mid-range logical infidelity remains 0.42-0.68x of the paper curve because the panel-(c) gate/idle schedule is reconstructed and the author implementation is unavailable. Runtime remains proxy timing; digitized source point sets are not redistributed.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig1 infidelity reproduction](outputs/figures/fig1_infidelity_reproduction.png)

![fig2 acceptance reproduction](outputs/figures/fig2_acceptance_reproduction.png)

![fig3 runtime reproduction](outputs/figures/fig3_runtime_reproduction.png)

![fig4 sampling precision reproduction](outputs/figures/fig4_sampling_precision_reproduction.png)

![steane exact acceptance comparison](outputs/figures/steane_exact_acceptance_comparison.png)

![steane exact acceptance reproduction](outputs/figures/steane_exact_acceptance_reproduction.png)

![steane exact infidelity comparison](outputs/figures/steane_exact_infidelity_comparison.png)

![steane exact infidelity reproduction](outputs/figures/steane_exact_infidelity_reproduction.png)
