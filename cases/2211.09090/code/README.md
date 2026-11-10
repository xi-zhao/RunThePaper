# Runnable code for 2211.09090

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2211.09090/code/requirements.txt
cd cases/2211.09090/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 原闭环参数和逐次离子读出缺失。高斯似然分母的因子差异需和闭环模型约定一并解读。
