# Independent reproduction of the dissipative two-photon Dicke transition

This case accompanies [arXiv:2412.14271](https://arxiv.org/abs/2412.14271) and
[Physical Review Letters 135, 173602 (2025)](https://doi.org/10.1103/mz92-6l9g).
It does not trace the paper's figures. It starts from the Hamiltonian, Lindblad
equation, and second-order cumulant equations, generates numerical objects
independently, and uses paper images only for post-run visual diagnosis.

## Reproduced scope

- Fig. 2: analytic one-photon-loss branches, cutoff-dependent trajectories,
  and Fock distributions;
- Fig. 3: finite-size distributions and thermodynamic both-loss branches;
- Fig. 4: Wigner functions computed from generated reduced density matrices;
- Figs. S1 and S2: Bogoliubov spectra of the fixed points;
- Fig. S5: trajectory-count convergence;
- pure two-photon-loss supplement: Liouvillian zero modes and parity sectors.

Seven of eight numerical figure groups have runnable, independently generated
artifacts. Formal supplemental Figs. S3–S4 remain blocked because their defining
parameters cannot be established. The main quantum panels use 6–16 trajectories
per job, so they are mechanism- and feature-level results rather than
paper-sample-count equivalents.

## Main scientific finding

The photon number of the dash-dotted lower curve in Fig. 3(g) identifies the
squeezed-high fixed point. It has no positive Bogoliubov eigenvalue in the
independent calculation, but it contains a photon zero mode. Along that mode,
$\dot r=0.4r^3+O(r^5)$, which makes the branch nonlinearly unstable. The plotted
classification is therefore defensible, while the paper's stated positive-
eigenvalue evidence is inconsistent with the accessible printed equations.
See the focused [discrepancy report](../docs/PAPER_DISCREPANCY.md).

## Quick run

From the RunThePaper repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install qutip
cd cases/2412.14271/code
python scripts/run_analytic.py
python scripts/render_figures.py
```

This fast path recomputes analytic branches and stability, then renders every
figure from the generated analytic data and the shipped frozen quantum arrays.
The complete quantum rerun is documented in [code/README](../code/README.md)
and takes roughly ten-plus minutes on the reference CPU.

The equation map is in [DERIVATION.md](../docs/DERIVATION.md), and the numerical
boundary is in [NUMERICAL_METHODS.md](../docs/NUMERICAL_METHODS.md). The final
foreground pixel score is 46.71/100, with full-canvas SSIM about 0.768. These
visual diagnostics do not replace the per-figure physics checks under
[`outputs/checks`](../outputs/checks/).

The public package contains no paper PDF, original figure, digitized curve, or
author numerical array. Paper images were used only after numerical arrays were
frozen and never supplied physical parameters or data values.
