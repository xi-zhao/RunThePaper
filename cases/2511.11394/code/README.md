# Runnable code for 2511.11394

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2511.11394/code
python scripts/run_reproduction.py --config config/exploratory_targets.json --target T001 --mode smoke --no-render --attested-stage exploratory
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Exact extended-Hubbard targets reproduce the paper at numerical-feature level. Main Fig. 1 remains partial because its energy normalization and t=15 rate conflict with the printed model.
