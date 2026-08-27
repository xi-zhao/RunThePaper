# Runnable code for cond-mat-0610854

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/cond-mat-0610854/code
python scripts/run_reproduction.py --config config/reduced_scale.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, parameters=mixed, parameter_provenance=missing, causal_resolution=terminal_blocker, execution=missing, pixel=passed_with_not_comparable, independent_review=stale, review_scope=stale, paper_assessment=stale.
