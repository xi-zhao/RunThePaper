# Runnable code for 1911.02005

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1911.02005/code/requirements.txt
cd cases/1911.02005/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 实机读出与谱标定仍缺。主入口复算可脱离参考曲线运行的单音和脉冲滤波块。
