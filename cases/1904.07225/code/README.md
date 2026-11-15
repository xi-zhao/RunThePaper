# Runnable code for 1904.07225

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1904.07225/code/requirements.txt
cd cases/1904.07225/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 这里的 Brier 分数评估公开读出的预测。原 SSIM 倍数仍需同期逐次地图和制图设置。
