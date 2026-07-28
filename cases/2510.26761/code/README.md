# Runnable code for 2510.26761

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2510.26761/code
python scripts/run_reproduction.py
python scripts/render_figures.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Main Fig. 2 is an analytic-reference reproduction. Main Fig. 1 uses exact state-derived fields but reconstructed three-dimensional presentation because the source omits isosurface levels and camera settings. The printed state implies a threshold numerator of 52 while the End Matter prints 56; the numerical negativity clears only the state-derived bound.
