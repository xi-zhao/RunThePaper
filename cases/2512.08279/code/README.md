# Runnable code for 2512.08279

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2512.08279/code
python scripts/run_reproduction.py --config config/paper_protocol.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Scientific similarity 95/100; pixel fidelity 85.72/100.
