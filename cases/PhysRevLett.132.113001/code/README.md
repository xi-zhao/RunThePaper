# Runnable code for PhysRevLett.132.113001

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/PhysRevLett.132.113001/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, numerical_scope=incomplete, parameters=mixed, science=failed, pixel=not_applicable, independent_review=missing, paper_assessment=missing.
