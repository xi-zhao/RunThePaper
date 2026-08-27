# Runnable code for 2005.12667

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2005.12667/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Formal RMP publication is used to identify corrections to arXiv Eqs. 29, 51, and 67. Source spectral figures do not specify absolute plotting parameters; similarity is therefore feature-level, not exact-parameter reproduction.
