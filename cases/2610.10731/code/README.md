# Runnable code for 2610.10731

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2610.10731/code/requirements.txt
cd cases/2610.10731/code
python scripts/run_reproduction.py
```

Reruns write to a new temporary directory and print its absolute path. Frozen evidence in ../outputs/ is preserved. See ../docs/NUMERICAL_METHODS.md for all run modes and output handling.

Boundary: Partial reproduction. Exact finite-circuit acceptance is not complete logical magic-state fidelity; equal author circuit/decoder conventions and low-error-rate resource curves remain unresolved.
