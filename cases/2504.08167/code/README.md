# Runnable code for 2504.08167

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2504.08167/code/requirements.txt
cd cases/2504.08167/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 原航迹、漂移与收敛需要同航次 GNSS、惯导和磁场记录。地图识别演示使用独立合成输入。
