# Runnable code for 2305.15556

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2305.15556/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Source images may be opened only after generated numerical data are frozen, and never feed the numerical runner.
