# Runnable code for 2608.05312

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2608.05312/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Mean hopping t=1 meV and source state |1> are reconstructed from cross-figure constraints and validated numerically. Exact author random seeds and optimization grids are unavailable, so generated artifacts are exploratory paper-subset evidence. Ten scored numerical targets pass with an overall similarity score of 83.4; the QCLE benchmark remains blocked by missing source inputs.
