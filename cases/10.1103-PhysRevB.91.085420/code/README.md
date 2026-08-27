# Runnable code for 10.1103-PhysRevB.91.085420

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/10.1103-PhysRevB.91.085420/code
python scripts/run_reproduction.py --config config/implementation_closure.json --output-root outputs/public_quick_run
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: parameters=paper_exact, causal_resolution=not_required, pixel=missing, independent_review=missing, review_scope=missing, paper_assessment=missing.
