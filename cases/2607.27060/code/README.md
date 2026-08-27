# Runnable code for 2607.27060

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2607.27060/code
python scripts/run_reproduction.py --config config/paper_exact_targets.json --target T-FIG002A --attested-stage final_reproduction
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, parameters=paper_exact, causal_resolution=not_required, independent_review=missing, review_scope=missing, paper_assessment=missing.
