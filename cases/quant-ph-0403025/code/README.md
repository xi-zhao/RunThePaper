# Runnable code for quant-ph-0403025

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/quant-ph-0403025/code
python scripts/run_reproduction.py --config config/paper_exact.json --output-root outputs/public_quick_run
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Author EPS/PDF pixels are comparison-only and never feed the numerical runner. All three numerical panels passed paper-exact science, isolated execution, and scientific-region render acceptance; fresh-context review remains pending.
