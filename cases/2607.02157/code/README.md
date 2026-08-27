# Runnable code for 2607.02157

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2607.02157/code
python scripts/run_reproduction.py --config config/implementation_probe.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, parameters=paper_exact, parameter_provenance=missing, causal_resolution=terminal_blocker, science=pending, execution=missing, pixel=missing, independent_review=missing, review_scope=missing, paper_assessment=missing.
