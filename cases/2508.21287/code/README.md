# Runnable code for 2508.21287

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2508.21287/code/requirements.txt
cd cases/2508.21287/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: H200 和原硬件对照仍需对应环境与精确输入。公开运行核验算法和计数。
