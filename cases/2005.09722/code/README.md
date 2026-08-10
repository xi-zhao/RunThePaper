# Runnable code for 2005.09722

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2005.09722/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: The L=200-800 and 5000-trajectory paper-scale channel is code-ready and smoke-tested; the final A100 campaign remains unexecuted.
