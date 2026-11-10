# Runnable code for 1909.10727

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1909.10727/code/requirements.txt
cd cases/1909.10727/code
python scripts/run_reproduction.py
```

Recalculates the pulse model, randomized benchmarking trials and centered autocorrelation into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 实机随机序列、AWG 波形与逐次读出未取得。实验误差幅度和五离子联合统计仍待核对。
