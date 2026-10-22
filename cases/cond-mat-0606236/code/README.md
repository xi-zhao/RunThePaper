# Runnable code for cond-mat-0606236

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/cond-mat-0606236/code/requirements.txt
cd cases/cond-mat-0606236/code
python scripts/run_reproduction.py
```

Fresh calculations write to a new directory. Frozen evidence is retained; see docs/NUMERICAL_METHODS.md.

Boundary: 数值样例支持指定公式，不能代替对所有无限维物理状态的一般性证明。
