# Runnable code for 1706.07435

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1706.07435/code
python scripts/run_reproduction.py --config config/independent_campaign.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: All 15 visible theory-numerical panels are frozen in the reproduction scope. Source figures are validation-only; generated values must come from formulas or independent eigensolvers.
