# 10.1103-PRXQuantum.6.010331: Benchmarking and Fidelity Response Theory of High-Fidelity Rydberg Entangling Gates

Preprint: [arXiv:2407.20184 — Benchmarking and Fidelity Response Theory of High-Fidelity Rydberg Entangling Gates](https://arxiv.org/abs/2407.20184)

Published as: [Benchmarking and Fidelity Response Theory of High-Fidelity Rydberg Entangling Gates](https://doi.org/10.1103/PRXQuantum.6.010331)

Formal citation: PRX Quantum 6, 010331 (2025) · DOI `10.1103/PRXQuantum.6.010331` · Locator `010331`

Public status: **Partial scientific reproduction** · Audit score: **79.89/100**

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

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/10.1103-PRXQuantum.6.010331/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Formal publication identity verified as PRX Quantum 6, 010331 (2025), DOI 10.1103/PRXQuantum.6.010331. Fig. 15 and Fig. 6(a) envelopes are reproduced from the paper-exact Appendix-L functions; those approximate fits omit small intensity side peaks, and the independent Hamiltonian diagnostic is reconstructed because the target-specific phase trajectory is not disclosed.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig10 spin lock filter](outputs/figures/fig10_spin_lock_filter.png)

![fig11 many body responses](outputs/figures/fig11_many_body_responses.png)

![fig12 cavity transfer](outputs/figures/fig12_cavity_transfer.png)

![fig15 direct diagnostic](outputs/figures/fig15_direct_diagnostic.png)

![fig15 universal response](outputs/figures/fig15_universal_response.png)

![fig17 phase flip first order](outputs/figures/fig17_phase_flip_first_order.png)

![fig6a scaled response](outputs/figures/fig6a_scaled_response.png)

![fig7 formula scalings](outputs/figures/fig7_formula_scalings.png)

![fig8 public anchor scaling](outputs/figures/fig8_public_anchor_scaling.png)

![fig9 protocol responses](outputs/figures/fig9_protocol_responses.png)
