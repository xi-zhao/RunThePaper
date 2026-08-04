# Phase transitions in nonreciprocal driven-dissipative condensates: an independent numerical reproduction

## Outcome

This case reconstructs the paper's nonreciprocal lattice model directly from
its equations. It covers the main numerical content of Main Figs. 1–6 and
Supplemental Figs. S1, S2(a), and S3. The result is a **partial full-paper
numerical reproduction**, not a complete reproduction: all 12 executed targets
pass their scientific checks, while four compute-intensive numerical items
remain open.

The normalized reproduction score is **76.75/100**. Across predeclared
scientific regions, mean grayscale pixel similarity is **86.56/100** and mean
SSIM is **0.5330**. Pixel metrics evaluate how faithfully independently
generated science was rendered; they cannot replace equation, parameter, or
dynamical checks.

## Reproduced content

- PBC and OBC complex spectra and vacuum thresholds from Eq. (1);
- nonlinear open-boundary dynamics, the static kink, and broad phase structure
  from Eq. (2);
- existence and Bogoliubov stability of PBC traveling waves;
- Lyapunov exponents, phase portraits, and particle-hole dynamics;
- supplemental critical-exceptional-point curves, chaotic domains, and edge
  dynamics.

Representative quantitative results include a static-kink exponent of
`-0.5045` (paper: `-0.5`), a dynamic frequency-versus-dispersion RMSE of
`0.00625`, and an independently measured particle-hole period of `26.655`
(paper: `26.66`).

## Findings from independent checks

1. The displayed 2×2 stability matrix requires `4 Lambda^2` in the eigenvalue
   radical, whereas the printed closed form contains only `Lambda^2`. The
   corrected expression agrees with direct diagonalization to `2.7e-15`.
2. The Fig. S1 caption's critical kappa values for `gamma=0.1` and `0.2` differ
   from independent Jacobian-zero locations by about `0.00671` and `0.00540`.
   The `gamma=0.3` value agrees within `4e-5`.

## Scientific boundary

The numerical programs do not read paper images, extracted curves, author
numerical code, or author-produced numerical datasets. Paper figures enter only
after generated arrays have been frozen, in a separate rendering comparison
that may tune layout and style but cannot change physical parameters or arrays.
The limited paper excerpts inside comparison boards validate structure rather
than author-data-level equivalence.

## Run

From this case's `code` directory, regenerate every public figure from the
included independent arrays:

```bash
python scripts/render_fast_formula_targets.py
python scripts/render_dynamic_targets.py
python scripts/render_cep_targets.py
python scripts/render_phase_diagram_targets.py
```

Recompute the implemented targets:

```bash
python scripts/run_fast_formula_targets.py
python scripts/run_dynamic_targets.py
python scripts/run_cep_targets.py
python scripts/run_phase_diagram_targets.py
```

The complete local run takes a few minutes; the dynamic stage peaks near
2.2 GiB. Outputs are written to `../outputs/data`, `../outputs/checks`, and
`../outputs/figures`.

## Remaining boundary

- the paper-resolution boundary in Main Fig. 3(a);
- the fine multistable stripes in Main Fig. 4(a);
- the complete five-attractor hierarchy in Main Fig. 4(d);
- the 300-nearby-trajectory ensemble in Supplemental Fig. S2(b).

This package is therefore a runnable and auditable scientific reproduction
with explicit limits, not a replacement for every author dataset and figure.
