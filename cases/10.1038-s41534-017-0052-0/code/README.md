# Runnable code for 10.1038-s41534-017-0052-0

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/10.1038-s41534-017-0052-0/code/requirements.txt
cd cases/10.1038-s41534-017-0052-0/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 原始 RB 和探测记录、实际实验约定以及原 Hessian 区间仍待核对。公开入口重算有限状态 RB 矩，GST 原计数沿用作者入口。
