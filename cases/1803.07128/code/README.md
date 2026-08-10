# Runnable code for 1803.07128

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install scikit-learn torch
cd cases/1803.07128/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Fig. 4 is paper-exact; Fig. 5--8 use printed methods with declared reconstructed metadata because seeds and critical training details are absent. Fresh-context independent review remains pending.
