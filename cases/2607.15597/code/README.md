# Runnable code for 2607.15597

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2607.15597/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Local feature reproduction scored 75.21/100; exact author-run equivalence remains blocked by missing MQDT, qLDPC, and open-system inputs.
