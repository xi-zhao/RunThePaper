# Runnable code for 2608.05435

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2608.05435/code/requirements.txt
cd cases/2608.05435/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 缺原实机样本、物理排程和相位校验。理想线路等价性与实机性能分开报告。
