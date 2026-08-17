# Runnable code for quant-ph-0211074

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/quant-ph-0211074/code
python scripts/run_reproduction.py --config config/smoke.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Full text and both numerical figures inventoried; formula gate 6/6 open. The printed XXX Hamiltonian sign and the Fig. 2 critical-curve description are under explicit consistency review.
