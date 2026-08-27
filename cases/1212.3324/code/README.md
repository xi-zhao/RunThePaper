# Runnable code for 1212.3324

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1212.3324/code
python scripts/run_reproduction.py --config config/paper_reconstructed.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: parameters=mixed, causal_resolution=terminal_blocker, science=failed, pixel=needs_repair, independent_review=stale, review_scope=stale, paper_assessment=stale.
