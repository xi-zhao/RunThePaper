# Independent BEM reproduction of dielectric-microcavity resonances

This case accompanies Jan Wiersig's
[arXiv:physics/0206018](https://arxiv.org/abs/physics/0206018) and
[Journal of Optics A 5, 53–60 (2003)](https://doi.org/10.1088/1464-4258/5/1/308).
It independently implements the Helmholtz Green function, boundary integral
equations, singular diagonal terms, and resonance reconstruction. Author code,
author arrays, digitized curves, and paper pixels are not numerical inputs.

## Reproduced scope

Figs. 1–4 are geometry or method schematics and are intentionally not redrawn.
All numerical figures are covered:

- Fig. 5: total plane-wave scattering cross section and resonance sequence;
- Fig. 6: near-field intensity reconstructed from a resonant boundary null state;
- Fig. 7: far-field radiation from the same generated boundary state.

The three targets pass independent physical checks: the linear residual is below
about $8\times10^{-15}$, the median optical-theorem relative error is about
0.073, the resonance singular value converges with resolution, the near field
has the expected interior/exterior contrast, and the far-field inversion
residual is below about $2\times10^{-9}$.

## Numerical boundary

The paper used roughly 1600 boundary elements but did not publish the exact
corner-rounding curve or nonuniform element map. This case explicitly uses
circular fillets and 432 constant elements. The feature run took about 159 s on
the reference CPU. It is therefore a reduced-scale scientific reproduction,
not a pointwise reconstruction of the paper's mesh.

After the numerical arrays are frozen, a RenderContract may adjust only canvas,
axes, typography, grayscale, line width, and interpolation. It cannot change
material parameters, mesh, resonance position, or field arrays. The final
foreground pixel score is 50.49/100 (raw comparable-target mean 58.16/100),
with full-image SSIM 0.7151. Sparse narrow peaks make line plots particularly
sensitive to small mesh-dependent shifts.

## Run

From the RunThePaper repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/physics-0206018/code
python scripts/run_all.py
python scripts/render_figures.py
```

See [DERIVATION.md](../docs/DERIVATION.md) for the equation map and
[NUMERICAL_METHODS.md](../docs/NUMERICAL_METHODS.md) for the evidence boundary.
Per-figure physics checks and pixel diagnostics are under
[`outputs/checks`](../outputs/checks/). The public package contains no paper PDF,
original figure, or source-derived data points.
