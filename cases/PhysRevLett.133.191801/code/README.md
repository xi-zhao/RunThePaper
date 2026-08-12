# Runnable code for PhysRevLett.133.191801

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/PhysRevLett.133.191801/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Unpublished experimental arrays are not reconstructed from source pixels. The inaccessible supplement prevents a complete full-paper numerical inventory.
