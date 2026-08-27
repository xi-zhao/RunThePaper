# Runnable code for 2103.03074

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2103.03074/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Canonical source switched to arXiv because it includes TeX source and original figure assets. Local reproduction validates formulas and numerical features, not the full 53-qubit GPU-scale contraction.
