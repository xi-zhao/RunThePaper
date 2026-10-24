# Runnable code for cond-mat-0506581

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/cond-mat-0506581/code/requirements.txt
cd cases/cond-mat-0506581/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: 示意图面板按科学内容核验，不做像素级复刻；相互作用扩展保留为原文的猜想层级。
