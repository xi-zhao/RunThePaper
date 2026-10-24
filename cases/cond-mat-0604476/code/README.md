# Runnable code for cond-mat-0604476

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/cond-mat-0604476/code/requirements.txt
cd cases/cond-mat-0604476/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: 数值样例和边界控制支持声明范围，不构成对无限维一般物理状态的形式证明。
