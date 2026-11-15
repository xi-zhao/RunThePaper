# Runnable code for 2209.06864

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2209.06864/code/requirements.txt
cd cases/2209.06864/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 缺原逐点变分角、部分分子模型约定和实机记录。可选 BeH₂ 复算使用 PySCF。
