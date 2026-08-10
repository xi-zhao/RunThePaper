# Runnable code for 1711.09418

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1711.09418/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Main Fig. 3 has a confirmed legend mismatch: final curves are sectors 4 and 5, not the printed 5 and 6. Fresh-context independent scientific review is still pending.
