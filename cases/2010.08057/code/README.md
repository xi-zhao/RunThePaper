# Runnable code for 2010.08057

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2010.08057/code/requirements.txt
cd cases/2010.08057/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 缺原硬件测量序列和读出。公开入口独立核对脉冲响应。
