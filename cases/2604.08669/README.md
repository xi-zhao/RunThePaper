# 2604.08669: An Algorithm for Fast Assembling Large-Scale Defect-Free Atom Arrays

Preprint: [arXiv:2604.08669 — An Algorithm for Fast Assembling Large-Scale Defect-Free Atom Arrays](https://arxiv.org/abs/2604.08669)

Formal publication: **Not recorded as of 2026-07-14**

Public status: **Partial scientific reproduction** · Audit score: **61.60/100**

Reproduces paper-geometry path-planning probes, paper-scale P2WGS continuity, and a pipelined timing model for atom-array assembly.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install torch
cd cases/2604.08669/code
python scripts/run_reduced_pilot.py
python scripts/run_reduced_p2wgs_pilot.py
python scripts/plot_reduced_outputs.py
python scripts/plot_completion_summary.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: The case includes an A100-SXM4-80GB 127x127 to 101x101 geometry probe and paper-scale P2WGS at N=10201. Full million-sample GNN training was stopped after the strict metric-contract gate failed; the unavailable GPU-parallel auction kernel is not replaced by CPU timing claims.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig3 a100 paper geometry gap](outputs/figures/fig3_a100_paper_geometry_gap.png)

![fig3 reduced gnn metrics](outputs/figures/fig3_reduced_gnn_metrics.png)

![fig4 paper scale p2wgs summary](outputs/figures/fig4_paper_scale_p2wgs_summary.png)

![fig4 reduced p2wgs continuity](outputs/figures/fig4_reduced_p2wgs_continuity.png)

![fig5 reduced timing model](outputs/figures/fig5_reduced_timing_model.png)
