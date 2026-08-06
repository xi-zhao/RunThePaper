# Runnable code for physics-0206018

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/physics-0206018/code
python scripts/run_all.py
python scripts/render_figures.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: The feature run uses 432 constant boundary elements rather than the paper's 1600 because the exact corner-rounding curve and nonuniform element map are not published; narrow resonance and far-field peaks therefore retain mesh-dependent shifts.
