# Runnable code for 2604.06319

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2604.06319/code/requirements.txt
cd cases/2604.06319/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 原始编译电路、逐门调度及噪声记录缺失。表 6 周期标签和非局部耦合器权重仍有差异。
