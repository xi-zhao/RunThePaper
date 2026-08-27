# Runnable code for 10.1007-s11433-024-2478-8

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/10.1007-s11433-024-2478-8/code
python scripts/run_reproduction.py --config config/scientific_closure.json --output-root outputs/public_quick_run
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, parameters=paper_exact, causal_resolution=repair_required, science=pending, pixel=not_comparable, paper_assessment=inconclusive.
