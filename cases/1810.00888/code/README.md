# Runnable code for 1810.00888

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1810.00888/code
python scripts/run_reproduction.py --config config/smoke.json --output outputs/public_quick_run
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: The isolated paper-scale run and fresh-context protocol-v2 review are recorded. T001/T002 and T006/T007 carry independently validated paper-error candidates; the remaining targets support the paper.
