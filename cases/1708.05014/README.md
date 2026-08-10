# 1708.05014: Boundary time crystals

Preprint: [arXiv:1708.05014 — Boundary time crystals](https://arxiv.org/abs/1708.05014)

Published as: [Boundary Time Crystals](https://doi.org/10.1103/PhysRevLett.121.035301)

Formal citation: Phys. Rev. Lett. 121, 035301 (2018) · DOI `10.1103/PhysRevLett.121.035301` · Locator `121, 035301`

Public status: **Partial scientific reproduction** · Audit score: **69.29/100**

All 24 numerical regions are formula-derived; quantum finite-size targets are reduced-scale, T009 is paper-exact, and phase portraits use printed couplings with independently reconstructed initials/sampling.

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

### main fig1 side by side comparison

![main fig1 side by side paper reference versus independent reproduction](docs/comparisons/main_fig1_side_by_side.png)

### main fig2 side by side comparison

![main fig2 side by side paper reference versus independent reproduction](docs/comparisons/main_fig2_side_by_side.png)

### main fig3 side by side comparison

![main fig3 side by side paper reference versus independent reproduction](docs/comparisons/main_fig3_side_by_side.png)

### main fig4 side by side comparison

![main fig4 side by side paper reference versus independent reproduction](docs/comparisons/main_fig4_side_by_side.png)

### supp fig s2 left side by side comparison

![supp fig s2 left side by side paper reference versus independent reproduction](docs/comparisons/supp_fig_s2_left_side_by_side.png)

### supp fig s2 right side by side comparison

![supp fig s2 right side by side paper reference versus independent reproduction](docs/comparisons/supp_fig_s2_right_side_by_side.png)

### supp fig s3 left side by side comparison

![supp fig s3 left side by side paper reference versus independent reproduction](docs/comparisons/supp_fig_s3_left_side_by_side.png)

### supp fig s3 right side by side comparison

![supp fig s3 right side by side paper reference versus independent reproduction](docs/comparisons/supp_fig_s3_right_side_by_side.png)

### supp fig s4 side by side comparison

![supp fig s4 side by side paper reference versus independent reproduction](docs/comparisons/supp_fig_s4_side_by_side.png)

### supp fig s5a side by side comparison

![supp fig s5a side by side paper reference versus independent reproduction](docs/comparisons/supp_fig_s5a_side_by_side.png)

### supp fig s5b side by side comparison

![supp fig s5b side by side paper reference versus independent reproduction](docs/comparisons/supp_fig_s5b_side_by_side.png)

### supp fig s5c side by side comparison

![supp fig s5c side by side paper reference versus independent reproduction](docs/comparisons/supp_fig_s5c_side_by_side.png)

### supp fig s5d side by side comparison

![supp fig s5d side by side paper reference versus independent reproduction](docs/comparisons/supp_fig_s5d_side_by_side.png)

### supp fig s6 side by side comparison

![supp fig s6 side by side paper reference versus independent reproduction](docs/comparisons/supp_fig_s6_side_by_side.png)

### supp fig s7a side by side comparison

![supp fig s7a side by side paper reference versus independent reproduction](docs/comparisons/supp_fig_s7a_side_by_side.png)

### supp fig s7b side by side comparison

![supp fig s7b side by side paper reference versus independent reproduction](docs/comparisons/supp_fig_s7b_side_by_side.png)

### supp fig s7c side by side comparison

![supp fig s7c side by side paper reference versus independent reproduction](docs/comparisons/supp_fig_s7c_side_by_side.png)

### supp fig s7d side by side comparison

![supp fig s7d side by side paper reference versus independent reproduction](docs/comparisons/supp_fig_s7d_side_by_side.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1708.05014/code
python scripts/run_reproduction.py --config config/feature.json
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 18 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Original figures are post-freeze render/comparison references only.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![main fig1 dynamics](outputs/figures/main_fig1_dynamics.png)

![main fig2 spectrum](outputs/figures/main_fig2_spectrum.png)

![main fig2 spectrum left](outputs/figures/main_fig2_spectrum_left.png)

![main fig2 spectrum left inset](outputs/figures/main_fig2_spectrum_left_inset.png)

![main fig2 spectrum right](outputs/figures/main_fig2_spectrum_right.png)

![main fig2 spectrum right inset](outputs/figures/main_fig2_spectrum_right_inset.png)

![main fig3 imag](outputs/figures/main_fig3_imag.png)

![main fig3 real](outputs/figures/main_fig3_real.png)

![main fig3 scaling](outputs/figures/main_fig3_scaling.png)

![main fig4 decay](outputs/figures/main_fig4_decay.png)

![main fig4 fft](outputs/figures/main_fig4_fft.png)

![main fig4 fft inset](outputs/figures/main_fig4_fft_inset.png)

![main fig4 fourier decay](outputs/figures/main_fig4_fourier_decay.png)

![supp branch cut](outputs/figures/supp_branch_cut.png)

![supp imaginary gap](outputs/figures/supp_imaginary_gap.png)

![supp phase means](outputs/figures/supp_phase_means.png)

![supp phase true centered variance diagnostic](outputs/figures/supp_phase_true_centered_variance_diagnostic.png)

![supp phase variances](outputs/figures/supp_phase_variances.png)

![supp phase wx a](outputs/figures/supp_phase_wx_a.png)

![supp phase wx b](outputs/figures/supp_phase_wx_b.png)

![supp phase wx c](outputs/figures/supp_phase_wx_c.png)

![supp phase wx d](outputs/figures/supp_phase_wx_d.png)

![supp phase wz a](outputs/figures/supp_phase_wz_a.png)

![supp phase wz b](outputs/figures/supp_phase_wz_b.png)

![supp phase wz c](outputs/figures/supp_phase_wz_c.png)

![supp phase wz d](outputs/figures/supp_phase_wz_d.png)

![supp real btc](outputs/figures/supp_real_btc.png)

![supp real strong](outputs/figures/supp_real_strong.png)
