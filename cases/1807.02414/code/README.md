# Runnable code for 1807.02414

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1807.02414/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: The solid curves use a declared collective-spin projection of the full spectral diffusion operator. External tDMRG markers are deferred and were not digitized or copied.
