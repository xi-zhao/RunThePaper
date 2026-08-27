# Runnable code for 2608.03987

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2608.03987/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Author Rust code and contraction plans are excluded from primary evidence. Figure 8 passed; Figure 9 produced 57/67 circuits below the paper threshold versus 66/67 in the source.
