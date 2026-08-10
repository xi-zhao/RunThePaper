# Runnable code for 1910.00020

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1910.00020/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Every target is independently generated from a phase-free binary stabilizer simulation; no author code, numerical arrays, or source pixels enter the runner. Published system sizes and unknown Monte Carlo metadata are reduced; Fig. 2(b) now uses exact mixed-stabilizer conditioning for an incomplete record. Fresh-context independent review remains pending.
