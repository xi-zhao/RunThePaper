# Runnable code for 2407.01296

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2407.01296/code
python scripts/run_reproduction_smoke.py
python scripts/run_supplementary_fig4.py
python scripts/run_supplementary_fig6.py
python scripts/run_supplementary_fig7.py --scale paper
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

The supplementary runners independently evaluate Eqs. (S24)-(S29), write to
the case-level output directories, and never read source-figure pixels or
digitized curves. The S7 runner uses fresh deterministic disorder samples and
records the caption's `N=935` versus exact-lattice `N=925` discrepancy. Focused
tests are under `tests/`.

Boundary: Supplementary Figs. S2 and S5 are not independently complete.
Supplementary Fig. S4 uses a finite-`L=160` OBC proxy for the grey
thermodynamic-limit series and is therefore scientifically partial. Fig. 2(d)
uses author-released ED tables, and unreported state selection, integer boundary
vertices, random seeds, probe grids, three-dimensional projection, and renderer
details limit pixel identity in Fig. 3 and several Fig. 4 panels.
