# Runnable code for 1807.10084

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1807.10084/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: All numerical subfigures are in scope; mixed schematics retain only formula-derived theoretical content. Original figures are reference-only. Author code and author numerical arrays are prohibited inputs.
