# Runnable code for 1706.07435

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1706.07435/code
python scripts/run_main_fig1.py
python scripts/run_main_fig2.py
python scripts/run_main_fig3.py
python scripts/run_supp_fig2.py
python scripts/run_supp_fig4.py
python scripts/run_supp_fig3.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: No author numerical arrays are available, so the scientific score is capped at 90 and does not claim author-data-level equivalence. The initial raster presentation score is 60.28; remaining differences are mainly aspect ratio, 3D camera, typography, and mesh or ink density. Supplement Fig. 1 and Supplement Table I are non-numerical context and are not reproduced as numerical targets.
