# Runnable code for 2605.04025

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2605.04025/code/requirements.txt
cd cases/2605.04025/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 图 S9 的格点和自旋标注仍有歧义，原实机 shots、高键维 TDVP 和多 GPU 计时待核。
