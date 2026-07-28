# Runnable code for 2512.08279

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install numpy scipy cvxpy scs matplotlib Pillow
cd cases/2512.08279/code
python scripts/run_reproduction.py
python scripts/render_figures.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: The paper publishes no machine-readable curve arrays or Monte Carlo seed. Source comparison therefore uses post-generation digitization; the stochastic Fig. 2 points are statistically equivalent rather than point-identical.
