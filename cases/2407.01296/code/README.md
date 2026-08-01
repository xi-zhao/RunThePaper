# Runnable code for 2407.01296

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2407.01296/code
python scripts/run_reproduction_smoke.py
python scripts/run_fig2d_finite_size.py
python scripts/run_supplementary_fig2.py
python scripts/run_supplementary_fig4.py
python scripts/run_supplementary_fig5.py
python scripts/run_supplementary_fig6.py
python scripts/run_supplementary_fig7.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Strict SSIM 0.95 pixel identity is not claimed. Main-text pixel-layout evidence covers 18 subplots; 17 supplementary subplots are explicitly deferred until separately cropped reference panels are frozen. Supplementary Fig. S7 records the caption's N=935 versus equation- and runner-consistent N=925 source discrepancy. Large Fig. 2(d) sparse determinants retain a double-precision LU-ordering-sensitive tail, and the exact Fig. S4 continuum is numerically traced on two finite energy grids.
