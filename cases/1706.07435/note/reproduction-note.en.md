# Complete numerical reproduction of non-Hermitian topological band theory

This case reproduces Shen, Zhen, and Fu, *Topological Band Theory for
Non-Hermitian Hamiltonians*, Phys. Rev. Lett. **120**, 146402 (2018). It is not
an image-tracing exercise. We first followed the derivations of the topological
invariants, generalized Dirac model, domain-wall matching, exceptional-point
vorticity, and lattice cylinder, then generated the numerical results from the
equations and independent eigensolvers.

## Scope

All reproducible theory-numerical content is covered: six targets and fifteen
numerical panels across Main Figs. 1–3 and Supplement Figs. 2–4. The schematic
Supplement Fig. 1 and contextual Supplement Table I are intentionally outside
the numerical scope. If a panel contains schematic or experimental material,
only its formula-defined theoretical part would be eligible.

## Scientific result

All six targets pass. Analytic spectra agree with sampled direct
diagonalization to at most $1.03\times10^{-15}$; the domain-wall common-spinor
residual is at most $1.43\times10^{-14}$; one loop exchanges the exceptional
point sheets and carries vorticity magnitude $1/2$; the exceptional-point pair
has charges $+1/2$ and $-1/2$; the hybrid-point directional exponents are
$0.5$ and $1.0$; and the paper-exact $80\times80$ cylinder eigensystems have a
maximum normalized residual of $1.60\times10^{-15}$ with minimum matched edge
weight $0.985$.

The scientific score is 90/100. It is capped because no author numerical arrays
are available, so the evidence supports an independent equation-level
reproduction rather than author-data-level equivalence. The initial raster
presentation score is 60.28/100 and separately tracks aspect ratio, 3D camera,
typography, and ink density.

## Run

```bash
cd cases/1706.07435/code
python -m unittest discover -s tests -v
python scripts/run_main_fig1.py
python scripts/run_main_fig2.py
python scripts/run_main_fig3.py
python scripts/run_supp_fig2.py
python scripts/run_supp_fig3.py
python scripts/run_supp_fig4.py
```

Each runner writes structured data and machine-readable checks before rendering
its figure. The public package contains no paper PDF, standalone source figure,
or digitized source curve, and the generation path accepts no paper image as an
input.

See the [derivation](../docs/DERIVATION.md), [numerical methods](../docs/NUMERICAL_METHODS.md),
and [score interpretation](../docs/SIMILARITY_SCORECARD.md).
