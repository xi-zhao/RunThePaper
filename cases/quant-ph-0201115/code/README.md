# Runnable code for quant-ph-0201115

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/quant-ph-0201115/code/requirements.txt
cd cases/quant-ph-0201115/code
python scripts/run_reproduction.py
```

Fresh calculations write to a new directory. Frozen evidence is retained; see docs/NUMERICAL_METHODS.md.

Boundary: 有限维数值核验不等于无限维定理的形式化证明。
