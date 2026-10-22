# Runnable code for 1902.10958

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1902.10958/code/requirements.txt
cd cases/1902.10958/code
python scripts/run_reproduction.py
```

Fresh calculations write to a new directory. Frozen evidence is retained; see docs/NUMERICAL_METHODS.md.

Boundary: 这仅核验带符号结果，不等于原图标签已对齐；降阶点和其余能带/环路比较仍保留。；Three complexR-loop geometry comparisons are now computed as source-only diagnostics; full original band, auxiliary-root and Lee spectrum comparisons remain.
