# Runnable code for 1608.02589

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1608.02589/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Second iteration reproduces core DTC rigidity features at L=14. Corrected endpoint mutual information reproduces the main finite-size-flow feature. Full phase diagram, scaling collapse, and critical exponents remain large-scale ED targets.
