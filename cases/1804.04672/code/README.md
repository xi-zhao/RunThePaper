# Runnable code for 1804.04672

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1804.04672/code
python scripts/run_reproduction.py --config config/implementation_closure.json --output outputs/public_quick_run
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, parameters=mixed, parameter_provenance=missing, causal_resolution=repair_required, science=pending, execution=failed, pixel=missing, independent_review=missing, review_scope=missing, paper_assessment=missing.
