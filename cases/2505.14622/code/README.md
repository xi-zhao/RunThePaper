# Runnable code for 2505.14622

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2505.14622/code/requirements.txt
cd cases/2505.14622/code
python scripts/run_reproduction.py
```

Writes fresh calculations and checks to a new directory; frozen published evidence is retained. See docs/NUMERICAL_METHODS.md.

Boundary: Both printed and steady-state-constrained parameter versions are retained. A 0.14% initial dip is resolved; the public notebook output grid skips it. Main acceleration results remain supported.
