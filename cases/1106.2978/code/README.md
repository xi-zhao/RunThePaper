# Runnable code for 1106.2978

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1106.2978/code
python scripts/run_reproduction.py --config config/paper_exact.json --output-root outputs/public_quick_run
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: artifact_integrity=artifact_invalid, parameters=paper_exact, causal_resolution=repair_required, science=pending, pixel=passed_with_not_comparable, paper_assessment=paper_error_candidate.
