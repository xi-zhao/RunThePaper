# Runnable code for 2406.01743

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2406.01743/code/requirements.txt
cd cases/2406.01743/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 加权边表与实机样本仍缺，当前只能定位 80 节点图表口径差异。
