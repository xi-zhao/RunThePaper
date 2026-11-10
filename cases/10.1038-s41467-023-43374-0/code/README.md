# Runnable code for 10.1038-s41467-023-43374-0

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/10.1038-s41467-023-43374-0/code/requirements.txt
cd cases/10.1038-s41467-023-43374-0/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 公开入口复跑模型核查。原始条纹、加速度记录、优化波形及实验校准仍缺，标度因子差异保留。
