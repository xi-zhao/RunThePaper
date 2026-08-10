# Runnable code for 1710.10890

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1710.10890/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: T005 retains an unresolved Main Fig. 3(b) branch-order mismatch. T007's frozen baseline is a declared proxy; a method-faithful 3D paper-scale implementation is code-ready. Main Fig. 4 is code-ready under an explicit N=4e5 assumption but paper-exact agreement remains blocked by unpublished per-curve atom numbers.
