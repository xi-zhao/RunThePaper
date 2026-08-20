# Runnable code for 0911.0556

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/0911.0556/code
python scripts/run_reproduction.py --config config/paper_reconstructed.json --output-root outputs/public_quick_run
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: The official arXiv archive contains manuscript TeX and three figure PDFs only; no author computational code or numerical arrays were found. Original-paper micromaser values N_ex and nu are omitted; the later public arXiv:1103.0919 parameter set N_ex=100, nu=0.15 is isolated as reconstructed provenance.
