# Runnable code for 2604.14094

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2604.14094/code/requirements.txt
cd cases/2604.14094/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 原裁剪实现、实机线路和逐次读出待核，两阶段规则是与图表相容的构造。
