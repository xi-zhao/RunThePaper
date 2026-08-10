# Runnable code for 1804.03151

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1804.03151/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Main Figure 1(c) is explicitly deferred because the exact DFT environment is under-specified. The numerical runner is isolated from paper-source figures and author numerical artifacts.
