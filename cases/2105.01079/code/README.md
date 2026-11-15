# Runnable code for 2105.01079

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2105.01079/code/requirements.txt
cd cases/2105.01079/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 原训练策略、器件标定、交错随机基准计数仍缺，公开运行采用说明中的独立模型。
