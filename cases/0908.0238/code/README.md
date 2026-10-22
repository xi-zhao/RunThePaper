# Runnable code for 0908.0238

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/0908.0238/code/requirements.txt
cd cases/0908.0238/code
python scripts/run_reproduction.py
```

Fresh calculations write to a new directory. Frozen evidence is retained; see docs/NUMERICAL_METHODS.md.

Boundary: 网格投影与近似阶次的残差仍需区分，未将量化对比完成当作整图完全一致。
