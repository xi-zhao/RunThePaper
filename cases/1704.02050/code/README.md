# Runnable code for 1704.02050

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1704.02050/code/requirements.txt
cd cases/1704.02050/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 逐次计数、实际控制和绝对谱幅校准缺失。公开入口复跑 DPSS 集中度和独立合成谱估计。
