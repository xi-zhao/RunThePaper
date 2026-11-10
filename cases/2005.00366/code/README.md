# Runnable code for 2005.00366

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2005.00366/code/requirements.txt
cd cases/2005.00366/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 精确原脉冲、优化初值、噪声及计时记录未取得。名义链长标度和同硬件运行时间分别看待。
