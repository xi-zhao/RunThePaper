# Runnable code for 1808.10462

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1808.10462/code/requirements.txt
cd cases/1808.10462/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 逐次计数、精确脉冲、原噪声波形和校准仍缺。连续失谐上界依赖明示的横向投影约定。
