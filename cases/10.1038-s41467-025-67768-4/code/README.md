# Runnable code for 10.1038-s41467-025-67768-4

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/10.1038-s41467-025-67768-4/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, numerical_scope=incomplete, parameters=mixed, parameter_provenance=missing, causal_resolution=repair_required, science=pending, pixel=missing, independent_review=missing, review_scope=missing, paper_assessment=missing.
