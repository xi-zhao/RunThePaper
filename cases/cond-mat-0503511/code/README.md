# Runnable code for cond-mat-0503511

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/cond-mat-0503511/code
python scripts/run_reproduction.py --config config/smoke.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: parameters=mixed, causal_resolution=terminal_blocker, pixel=needs_repair, paper_assessment=mixed.
