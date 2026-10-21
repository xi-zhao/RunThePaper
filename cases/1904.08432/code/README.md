# Runnable code for 1904.08432

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1904.08432/code/requirements.txt
cd cases/1904.08432/code
python scripts/run_reproduction.py
```

Writes fresh calculations and checks to a new directory; frozen published evidence is retained. See docs/NUMERICAL_METHODS.md.

Boundary: Finite-ring reference conventions are explicit. Fig. 3(a) periodic L=30 is inferred, not author-confirmed. Source is arXiv v2; final journal text was not compared verbatim.
