# Runnable code for 2407.01296

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2407.01296/code
python scripts/run_reproduction.py --config config/final_resolution.json --profile attestation --output-root outputs/public_quick_run
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Fig. 2(c) uses the paper 101x101 grid and 200 momentum samples; mean hierarchical-potential errors against finite OBC are 0.00667/0.00623. Author Zenodo outputs are reference comparators only; generated evidence is independent numerics.
