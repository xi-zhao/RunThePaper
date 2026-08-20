# Runnable code for 1508.03344

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1508.03344/code
python scripts/run_reproduction.py --config config/reduced_all_targets.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: The arXiv archive contains manuscript TeX and vector figures only; no author computational code or numeric arrays were accessed.
