# Runnable code for 1905.09460

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1905.09460/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: The two Main Figure 2 schematic axes are context-only. Original source pixels are isolated to terminal evaluation and never feed numerical generation. Main Figure 3 and Supplement Figure S1 remain feature-level because the source omits transient controls and the edge-state classifier.
