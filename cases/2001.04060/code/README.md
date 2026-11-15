# Runnable code for 2001.04060

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2001.04060/code/requirements.txt
cd cases/2001.04060/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 缺原多 GPU 计时、实测控制，以及个别原出图波形设置。公开默认运行核对 Walsh 模型。
