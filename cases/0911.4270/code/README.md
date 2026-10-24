# Runnable code for 0911.4270

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/0911.4270/code/requirements.txt
cd cases/0911.4270/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: 数值和解析控制支持声明范围；Witness 是充分性判据，不排除所有不可分演化。
