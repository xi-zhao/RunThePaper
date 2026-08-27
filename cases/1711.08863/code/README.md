# Runnable code for 1711.08863

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1711.08863/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Whole-paper atomic audit: 4 eligible items, 4 reproduced; coverage 100.00%, fidelity and degree 87.66. T002-T004 use exact all-size witnesses plus isolated numerical sanity checks and do not require raster targets. Artifact and scientific checks pass for T001-T004; fresh-context independent review remains a lifecycle gate.
