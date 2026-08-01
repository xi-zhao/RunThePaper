# Non-Hermitian skin effect in arbitrary dimensions — reproduction note

## Result

This case completes a scientific reproduction of the formal paper's main-text
Figs. 1–5. Figs. 2(a–c), 3, and 4(a–f) are recomputed from the published model
with Python/SciPy. Figs. 1 and 5 are analytic schematic redraws. Fig. 2(d) is the
only source-assisted numerical panel: it uses author-released finite-size ED
tables, while the displayed observable is recomputed by this case. The current
extension also independently computes Supplementary Fig. S4 from Eqs.
(S24)-(S26) and Supplementary Fig. S6 from Eq. (S28).

This is not a pixel copy of the paper. Every formal canvas is registered to the
published dimensions, but none passes the strict `SSIM >= 0.95` threshold. The
main-text scientific evidence chain is complete. Supplementary Fig. S6 passes
its equation-level winding and Fermi-charge checks. Supplementary Fig. S4 is
scientifically partial: its caption sizes and inverse-size localization scaling
are reproduced, but the grey thermodynamic-limit series is honestly represented
by an independently calculated finite-`L=160` proxy. Supplementary Figs. S2,
S5, and S7 remain open.

## Supplementary equation checks

For Supplementary Fig. S4, the code constructs the coupled-chain OBC matrix in
Eq. (S24), diagonalizes every caption size `L=20,40,60,80`, and fits the central
state's inverse localization length to Eq. (S25). The fit gives `R²=0.9990`, an
intercept of `-0.00559`, and selected-eigenpair residuals below `3.7e-15`.

For Supplementary Fig. S6, the code evaluates the closed-loop phase winding in
Eq. (S28) on independently sampled momentum slices and solves the zeros of the
complex Bloch Hamiltonian. The normal model has winding values `{0,1}` and two
oppositely charged Fermi points; the critical rhombus model has `{-1,1}` and
four points with balanced total charge.

## How Fig. 3 is drawn

The current version addresses the line construction in Fig. 3(a) and the view
of Fig. 3(b):

- Fig. 3(a) projects regular `101 x 101` momentum grids onto the two beta planes
  instead of connecting irregular inverse-solver points;
- Fig. 3(b) uses periodic seam-free interpolation for the momentum surfaces;
- the 3D camera is fixed at `24°` elevation and `-41°` azimuth with equal axis
  proportions.

All scientific gates pass, while the full-figure SSIM remains `0.6969`. The
status is therefore `pixel_registered_not_identical`. Sampling, interpolation,
projection, font rasterization, and antialiasing remain visible sources of
pixel difference.

## How Fig. 4 is drawn

All six Fig. 4 panels pass their independent numerical checks. The full-figure
SSIM is `0.5823`; panel SSIM values are `0.9107`, `0.5717`, `0.7042`, `0.4353`,
`0.4181`, and `0.4946`. The lower-scoring panels depend on unreported choices
such as the state sequence, integer boundary vertices, random realization,
energy-probe grid, and exact typesetting. These uncertainties are disclosed in
the machine checks instead of being hidden by copying paper pixels.

## Public boundary

The public package contains clean-room numerical kernels, lightweight runners,
generated data, generated figures, machine checks, and limited attributed
comparison boards. It excludes the paper PDF, standalone original figures,
vector paths, digitized curves, and private process history. Comparison pixels
are used only for presentation audits and never enter the numerical model.

## Quick run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2407.01296/code
python scripts/run_reproduction_smoke.py
python scripts/run_supplementary_fig4.py
python scripts/run_supplementary_fig6.py
```

The smoke runner checks reduced-scale Fig. 2 geometry and Fig. 4(d). The two
supplementary runners reproduce S4 and S6 at the declared scientific settings.
Paper-scale generated results are included in the case. See
[`../docs/NUMERICAL_METHODS.md`](../docs/NUMERICAL_METHODS.md) and
[`../docs/SIMILARITY_SCORECARD.md`](../docs/SIMILARITY_SCORECARD.md) for the
method and evidence boundary.
