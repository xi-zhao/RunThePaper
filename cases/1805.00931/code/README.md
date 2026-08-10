# Runnable code for 1805.00931

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1805.00931/code
python scripts/run_reproduction.py --config config/feature.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Table I is paper-exact; Figures 2 and 3 are reduced-scale exploratory artifacts. Fresh-context independent review and paper-scale Figure 2/3 runs remain pending.
