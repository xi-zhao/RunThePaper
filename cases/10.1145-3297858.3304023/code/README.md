# Runnable code for 10.1145-3297858.3304023

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/10.1145-3297858.3304023/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: parameters=mixed, parameter_provenance=failed, causal_resolution=terminal_blocker, execution=missing, pixel=missing, independent_review=missing, review_scope=missing, paper_assessment=missing.
