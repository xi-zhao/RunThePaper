# Runnable code for 2412.14271

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install qutip
cd cases/2412.14271/code
python scripts/run_analytic.py
python scripts/render_figures.py
```

## Full reduced-ensemble rerun

Regenerates all shipped analytic and quantum arrays with the declared public configurations. The quantum jobs take roughly ten-plus minutes on the reference CPU and remain reduced relative to the paper's trajectory counts.

```bash
cd cases/2412.14271/code
python scripts/run_analytic.py
python scripts/run_quantum_one_photon.py
python scripts/run_quantum_main.py
python scripts/run_quantum_parity.py
python scripts/render_figures.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Main quantum panels use reduced trajectory counts, formal supplemental Figs. S3–S4 remain blocked by unavailable defining parameters, and the Fig. 3(g)/Fig. S2 evidence discrepancy awaits independent review or author clarification.
