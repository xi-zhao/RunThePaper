# Runnable code for 1708.05014

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1708.05014/code
python scripts/run_reproduction.py --config config/feature.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Original figures are post-freeze render/comparison references only.
