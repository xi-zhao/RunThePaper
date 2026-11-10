# Runnable code for 2508.16505

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2508.16505/code/requirements.txt
cd cases/2508.16505/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 原规模的独立电路搜索、稀疏化和计时仍未完成。公开矩阵的验证属于条件检查，当前原生记录没有正式逐对象评定。
