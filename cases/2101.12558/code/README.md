# Runnable code for 2101.12558

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2101.12558/code
python scripts/run_reproduction.py --config config/feature.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Paper-scale execution is deferred because indispensable inputs and a full DFT+DMFT campaign are absent.
