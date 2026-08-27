# Runnable code for 0709.0548

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/0709.0548/code
python scripts/run_reproduction.py --config config/paper_scale.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, parameters=mixed, parameter_provenance=missing, causal_resolution=repair_required, science=pending, execution=failed, pixel=needs_repair, independent_review=stale, review_scope=stale, paper_assessment=mixed.
