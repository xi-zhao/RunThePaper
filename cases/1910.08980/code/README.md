# Runnable code for 1910.08980

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1910.08980/code
python scripts/run_reproduction.py --config config/paper_protocol.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: All numerical scope is independently reproduced; paper-exact completion is blocked by unpublished random-instance identity and a missing fresh-context review.
