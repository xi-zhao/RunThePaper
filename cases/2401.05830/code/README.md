# Runnable code for 2401.05830

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2401.05830/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Author source code and numerical arrays are outside the allowed evidence boundary.
