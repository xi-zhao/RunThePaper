# Runnable code for 1709.03478

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1709.03478/code
python scripts/run_reproduction.py --config config/feature_run.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Fig. 4 theory is partial and experimental panels are blocked by missing author data.
