# Runnable code for 1903.05124

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1903.05124/code
python scripts/run_supp_fig_s2.py --render-only
python scripts/run_supp_fig_s3.py --render-only
python scripts/run_supp_fig_s4.py --refinement-input ../outputs/data/supp_fig_s5_refinement_numerical_data.csv
python scripts/run_supp_fig_s5.py --refinement-input ../outputs/data/supp_fig_s5_refinement_numerical_data.csv
```

## Full mixed-scale rerun

The full mixed-scale campaign takes roughly 50 CPU wall-clock minutes with eight workers on the recorded machine. It reruns T002/T003 at paper scale and T001/T004/T005/T006 at their published feature scales, writes generated data and checks before figures, and never reads a paper image.

```bash
cd cases/1903.05124/code
python scripts/run_main_fig2.py --scale feature --workers 8
python scripts/run_supp_fig_s2.py --scale paper --workers 8
python scripts/run_supp_fig_s3.py --scale paper --workers 8
python scripts/run_supp_fig_s5_refinement.py --workers 8
python scripts/run_supp_fig_s4.py --refinement-input ../outputs/data/supp_fig_s5_refinement_numerical_data.csv
python scripts/run_supp_fig_s5.py --refinement-input ../outputs/data/supp_fig_s5_refinement_numerical_data.csv
python scripts/run_supp_fig_s6.py --scale feature --workers 8
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: T001, T004, T005, and T006 use reduced statistics or system sizes through L=24, so the package does not claim paper-exact precision for all panels. T005 transition locations pass, but the fitted critical exponent remains too depth-sensitive for a full exponent claim. Author seeds and raw trajectories are unavailable, and the S3 caption/raster uncertainty-label inconsistency is recorded explicitly.
