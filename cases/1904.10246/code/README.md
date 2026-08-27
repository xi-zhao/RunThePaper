# Runnable code for 1904.10246

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1904.10246/code
python scripts/run_reproduction.py --target T_FIG2 --config config/implementation.json --smoke
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Raw inputs frozen for baseline-fast-2026-07-29; keep case in mapping_pending until its isolated trial starts.
