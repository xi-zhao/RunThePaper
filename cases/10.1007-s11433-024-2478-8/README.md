# 10.1007-s11433-024-2478-8: Buffer-atom-mediated quantum logic gates with off-resonant modulated driving

Preprint: **No preprint recorded as of 2026-07-14**

Published as: [Buffer-atom-mediated quantum logic gates with off-resonant modulated driving](https://doi.org/10.1007/s11433-024-2478-8)

Formal citation: Sci. China-Phys. Mech. Astron. 67, 120311 (2024) · DOI `10.1007/s11433-024-2478-8` · Locator `Article 120311`

Public status: **Partial scientific reproduction** · Audit score: **84.60/100**

Reproduces the buffer-atom-mediated CZ gate from an independent three-body Rydberg Hamiltonian: single-photon waveforms, populations, and phases (Fig. 3, complete, gate error < 1e-4), the two-photon protocol (Fig. 4), the Doppler-insensitive dual-pulse upgrade (Fig. 5), and the amplitude-ratio robustness map (Fig. 7).

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

The left column in each panel is a limited excerpt from Y. Sun, [Sci. China-Phys. Mech. Astron. 67, 120311 (2024)](https://doi.org/10.1007/s11433-024-2478-8); the right column is generated independently from this case. These comparisons validate physical structure and key numerical features, not author-data-level or point-for-point equivalence.

### Fig. 3 (single-photon CZ) comparison

![Fig. 3 (single-photon CZ) paper reference versus independent reproduction](docs/comparisons/fig3_singlephoton_comparison.png)

### Fig. 4 (two-photon CZ) comparison

![Fig. 4 (two-photon CZ) paper reference versus independent reproduction](docs/comparisons/fig4_twophoton_comparison.png)

### Fig. 5 (dual-pulse Doppler) comparison

![Fig. 5 (dual-pulse Doppler) paper reference versus independent reproduction](docs/comparisons/fig5_dualpulse_comparison.png)

### Fig. 7 (robustness colormap) comparison

![Fig. 7 (robustness colormap) paper reference versus independent reproduction](docs/comparisons/fig7_robustness_comparison.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/10.1007-s11433-024-2478-8/code
python scripts/run_fig3.py
python scripts/run_fig4.py
python scripts/run_fig5.py
python scripts/run_fig7.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 4 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: The two-photon full three-level model gives gate error ~1e-3 vs the paper's <1e-4 (its waveforms were likely optimised in a reduced/effective model); Fig. 7 peak ~25% below the paper; Fig. 6 three-qubit Toffoli geometry is underspecified and not reproduced; Figs. a6-a8 have no published coefficients.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig3 amplitude](outputs/figures/fig3_amplitude.png)

![fig3 hybrid](outputs/figures/fig3_hybrid.png)

![fig3 paper style](outputs/figures/fig3_paper_style.png)

![fig4 paper style](outputs/figures/fig4_paper_style.png)

![fig5 paper style](outputs/figures/fig5_paper_style.png)

![fig7 scan](outputs/figures/fig7_scan.png)
