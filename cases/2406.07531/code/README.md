# Runnable code for 2406.07531

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2406.07531/code
python scripts/run_reproduction.py --config config/feature.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: APS supplement returned HTTP 403 locally and through the authorised institutional Jupyter network; Tables S6/S7 remain missing source material. No public author source code or point-level numerical arrays were found in the arXiv archive.
