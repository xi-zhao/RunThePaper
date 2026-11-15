# Runnable code for 2010.04375

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2010.04375/code/requirements.txt
cd cases/2010.04375/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 公开均值支持约 5.25 kHz 和 31.3–31.5 kHz 峰，原 AOM 相位指令和逐次测量待核。
