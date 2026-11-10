# Runnable code for 1712.01291

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1712.01291/code/requirements.txt
cd cases/1712.01291/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 原模拟轨迹、训练配置与调参档案缺失。全案保留冻结检查点，公开入口重算周期 GP，其他预测器的原条件仍有差异。
