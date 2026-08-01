# Runnable code for 2407.01296

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2407.01296/code
python scripts/run_reproduction_smoke.py
python scripts/run_supplementary_fig2.py
python scripts/run_supplementary_fig4.py
python scripts/run_supplementary_fig6.py
python scripts/run_supplementary_fig7.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Supplementary Fig. S5 remains open, Fig. S4 retains a declared large-L proxy for its exact TDL line, and Fig. 2(d) uses author-released ED tables. Supplementary Fig. S7 records the caption's N=935 versus equation- and runner-consistent N=925 source discrepancy. Unreported state selection, integer boundary vertices, random seeds, probe grids, three-dimensional projection, and renderer details limit pixel identity in several panels.
