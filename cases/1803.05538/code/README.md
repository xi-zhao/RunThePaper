# Runnable code for 1803.05538

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1803.05538/code/requirements.txt
cd cases/1803.05538/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 同期参数和原始模拟轨迹未取得。保留 SIN 交叉项和标量高斯似然符号差异。
