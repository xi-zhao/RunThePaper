# Runnable code for 1206.2505

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1206.2505/code
python scripts/run_reproduction.py --config config/paper_scale.json --output-root outputs/public_quick_run
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Fresh-context review is the remaining lifecycle gate.
