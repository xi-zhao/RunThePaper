# Runnable code for 2602.12212

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2602.12212/code
python scripts/run_reproduction.py --config config/paper_scale_closure.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: All active v3 numerical figures were regenerated independently at the paper's published sizes. Boundary, shell-edge, and confidence-interval conventions omitted by the paper are disclosed reconstructions.
