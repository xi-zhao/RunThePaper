# Runnable code for 2607.00718

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2607.00718/code
python scripts/run_reproduction.py T001 --device cpu
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: First milestone targets T001, T002C, T003, and T004. Zenodo transmission arrays appear to belong to an older manuscript version.
