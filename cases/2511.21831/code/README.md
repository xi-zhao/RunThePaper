# Runnable code for 2511.21831

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2511.21831/code/requirements.txt
cd cases/2511.21831/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 缺原门校准和逐次测量，图 8 改善倍数仍受观测量与图注口径影响。
