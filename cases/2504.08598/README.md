# 2504.08598: Graph coloring via quantum optimization on a Rydberg-qudit atom array

Preprint: [arXiv:2504.08598 — Graph coloring via quantum optimization on a Rydberg-qudit atom array](https://arxiv.org/abs/2504.08598)

Published as: [Graph coloring via quantum optimization on a Rydberg-qudit atom array](https://doi.org/10.1088/2058-9565/ae3b6d)

Formal citation: 11 (2), 025012 (2026) · DOI `10.1088/2058-9565/ae3b6d` · Locator `025012`

Public status: **Partial scientific reproduction** · Audit score: **81.00/100**

A clean-room Eq. (3)-Eq. (6) run reproduces Main Figures 5 and 6 at feature level; author CSVs are comparison-only after generation is frozen. Appendix Figures 8 and 9 retain stable named numeric mismatches, and Figure 7 is source-blocked.

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
cd cases/2504.08598/code
python scripts/run_reproduction.py --config config/clean_room_reproduction.json --output-root outputs/public_quick_run
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Figure 8 curve E/F and distribution E, and Figure 9 distribution H remain named mismatches. Pasqal/Pulser qubit validation is not applicable to the multilevel qudit Hamiltonian; no real hardware or advantage claim.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig5 k3 annealing reproduction](outputs/figures/fig5_k3_annealing_reproduction.png)
