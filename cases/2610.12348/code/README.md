# Runnable code for 2610.12348

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2610.12348/code/requirements.txt
cd cases/2610.12348/code
python scripts/run_reproduction.py
```

Reruns write to a new temporary directory and print its absolute path. Frozen evidence in ../outputs/ is preserved. See ../docs/NUMERICAL_METHODS.md for all run modes and output handling.

Boundary: Partial reproduction. Raw trajectory entropy is a normalization diagnostic, not physical von Neumann entropy. H3 large-ensemble/cutoff verification, remaining source figures and source-convention ambiguities remain open.
