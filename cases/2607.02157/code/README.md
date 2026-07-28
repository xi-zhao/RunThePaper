# Runnable code for 2607.02157

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install torch
cd cases/2607.02157/code
python scripts/run_scan.py
python scripts/run_nmse.py
python scripts/run_figS1.py
python scripts/plot_figures.py
python scripts/adjudicate_pooling.py
python scripts/verify_formulas.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Comparison is a feature contract against the paper's raster panels (no author data or tables), so each target is capped at 80. Fig. S1 uses 400 rather than 5000 drive sequences, 2500 rather than 5000 samples, and 400 rather than 10000 TFIM realizations; the paper also leaves F(omega) normalization unspecified. Fig. 2 retains a nonessential amplitude mismatch: the TFIM irreversible-work peak is 0.396 versus a visual paper reading near 0.49.
