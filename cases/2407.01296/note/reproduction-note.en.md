# Non-Hermitian skin effect in arbitrary dimensions — reproduction note

## Result

This case completes a scientific reproduction of the formal paper's main-text
Figs. 1–5. Figs. 2(a–d), 3, and 4(a–f) are recomputed from the published model
with Python/SciPy. Figs. 1 and 5 are analytic schematic redraws. No generated
numerical panel consumes author ED tables, digitized curves, or publication
pixels.

For Fig. 2(d), all 317 energy probes are independently evaluated from sparse
finite-OBC `log|det(H_L-E)|/N` and Eq. (10). A three-ordering sparse-LU audit
selects the numerically reliable fit prefix without consulting the expected
trend; every unstable large-size tail value remains in the public data and is
marked in the figure. All ten reliable fits have `R²>0.9988` and extrapolated
intercepts below `6.3e-4` in magnitude.

This is not a pixel copy of the paper. Every formal canvas is registered to the
published dimensions, but none passes the strict `SSIM >= 0.95` threshold. The
main-text scientific evidence chain is complete. Supplementary Figs. S2, S5,
S6, and S7 are now independently reproduced; Fig. S4 retains a declared
large-`L` proxy for its exact TDL line.

Supplementary Fig. S2 is generated from Eqs. (S14)–(S22): an exact separable
`N=5625` spectrum, exact and Amoeba spectral densities, and winding-classified
holes for both caption energies. Released author arrays are read only by a
separate post-generation comparison and never by the reproduction runner.

Supplementary Fig. S5 is generated from the formal Eq. (S27) and Eq. (10):
two exact `N=6400/6385` spectra, normal/scale-free broadening over 11 sizes, a
rhombus cut-edge state, and two spectral densities. A/B states are selected by
minimum/maximum RMS width in declared local windows without inspecting source
pixels. The differently parameterized legacy model in the author release is
excluded from generated inputs.

## Supplementary equation checks

For Supplementary Fig. S4, the code constructs the double-chain OBC matrix in
Eq. (S24), covers every caption length `L=20,40,60,80`, and fits the central
state's inverse localization length following Eq. (S25). The fit gives
`R²=0.9990`, intercept `-0.00559`, and selected eigenpair residuals below
`3.7e-15`; the grey thermodynamic-limit curve remains explicitly labeled as a
finite-`L=160` proxy.

For Supplementary Fig. S6, Eq. (S28) is evaluated on independently sampled
momentum slices and the complex Bloch zeros are solved without source curves.
The normal model has winding values `{0,1}` and two oppositely charged Fermi
points; the critical rhombic model has values `{-1,1}`, four Fermi points, and
balanced total charge.

For Supplementary Fig. S7, left and right eigensystems are solved at all six
paper sizes and Eq. (S29) is evaluated with 100 fresh uniform-disorder samples
per size. The normal response changes by only `0.37%`, while the critical
response grows from `3.40` to `356.17` and reaches `705x` the largest normal
response. Author arrays are used only after generation for slope validation.
The caption's `N=935` conflicts with the exact lattice and released `r=43`
runner, which both give `N=925`; the discrepancy is recorded explicitly.

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
python scripts/run_fig2d_finite_size.py --scale smoke
python scripts/run_supplementary_fig2.py --scale smoke
python scripts/run_supplementary_fig4.py
python scripts/run_supplementary_fig5.py --scale smoke --workers 4
python scripts/run_supplementary_fig6.py
python scripts/run_supplementary_fig7.py --scale paper
```

These commands run the reduced main-text and Fig. 2(d) smoke checks, fast S2/S5
formula checks, and the independent S4/S6/S7 supplementary calculations. Paper-scale generated
results are included in the case. See
[`../docs/NUMERICAL_METHODS.md`](../docs/NUMERICAL_METHODS.md) and
[`../docs/SIMILARITY_SCORECARD.md`](../docs/SIMILARITY_SCORECARD.md) for the
method and evidence boundary.
