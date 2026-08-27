# Runnable code for 2412.14271

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2412.14271/code
python scripts/run_reproduction.py --config config/analytic.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Main quantum figures are feature-level because trajectory counts are reduced. Formal Supplement Fig. S3 is an explicit uncovered item because its panel inventory, observable, and parameters are unavailable. Formal Supplement Fig. S4 is an explicit uncovered item because its panel inventory, observable, and parameters are unavailable. Fig. 3(g)/Fig. S2 has a confirmed branch-to-spectrum evidence discrepancy: the plotted lower branch is nonlinearly unstable but has no positive Bogoliubov eigenvalue.
