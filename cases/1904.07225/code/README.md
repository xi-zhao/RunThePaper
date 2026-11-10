# Runnable code for 1904.07225

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1904.07225/code/requirements.txt
cd cases/1904.07225/code
python scripts/run_reproduction.py
```

Default run repeats square-field held-out trials at frozen settings. The optional six-ion and camera runs use pinned author files. See docs/NUMERICAL_METHODS.md.

Boundary: 逐档重调的最大预算比分别为方形场 1.75、六离子 1.49。原仿真轨迹、历史滤波和制图配置、原拟合森林与选帧未取得。
