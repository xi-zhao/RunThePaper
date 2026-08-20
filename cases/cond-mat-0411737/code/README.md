# Runnable code for cond-mat-0411737

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/cond-mat-0411737/code
python scripts/run_reproduction.py --config config/paper_reconstructed.json --output-root outputs/public_quick_run
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Full PDF and source inventory audited; one numerical figure target (T001). Author source archive contains manuscript TeX and rendered EPS only, with no computational code or numeric arrays. Clean-room zigzag ribbon solver and paper-scale local run contract implemented; formal isolated run pending.
