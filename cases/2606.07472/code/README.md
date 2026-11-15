# Runnable code for 2606.07472

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2606.07472/code/requirements.txt
cd cases/2606.07472/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 原脉冲时序和 Tunnel Falls 标定仍缺。拟合对时序约束敏感，公开入口复算独立脉冲模型。
