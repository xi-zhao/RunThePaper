# Runnable code for 2401.08523

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2401.08523/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: All two main figures and all four numerical panels are generated from the paper's closed-form equations. The supplement contains derivations but no additional figures. Original source figures are isolated to terminal pixel evaluation and are never numerical inputs.
