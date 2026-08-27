# Runnable code for 10.1126-science.aaw1611

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/10.1126-science.aaw1611/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Published article and 35-page supplementary material ingested from institutional mirrors and recorded by SHA-256. The full paper and supplement contain 38 independently computable theoretical numerical items; all 38 have atomic targets and generated data. Experimental hardware measurements and raw tomography are excluded from the numerical-runner denominator. The current isolated CPU run attests all 38 targets; the historical A100 result is backend-portability evidence only. Twelve S20 panels retain an unresolved printed-time/source discrepancy, and S11 lacks author realization-level parameters.
