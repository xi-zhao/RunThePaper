# Runnable code for PhysRevLett.61.2015

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/PhysRevLett.61.2015/code/requirements.txt
cd cases/PhysRevLett.61.2015/code
python scripts/run_reproduction.py
```

Fresh calculations write to a new directory. Frozen evidence is retained; see docs/NUMERICAL_METHODS.md.

Boundary: 箭头与带符号Hall约定的视觉确认仍未完成；这是具体来源获取限制，不是作者未说明的证据。
