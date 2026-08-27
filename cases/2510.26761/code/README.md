# Runnable code for 2510.26761

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2510.26761/code
python scripts/run_reproduction.py T001
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: The numerical fields behind Main Fig. 1 are reproduced at feature level; the source does not disclose its isosurface rendering parameters. The printed Fig. 1 state implies (75*sqrt(2)+52)/600, while the End Matter prints (75*sqrt(2)+56)/600. The state-derived negative volume is 0.26369957: above the corrected bound and below the printed bound.
