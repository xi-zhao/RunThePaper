# Runnable code for PhysRevLett.67.516

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/PhysRevLett.67.516/code/requirements.txt
cd cases/PhysRevLett.67.516/code
python scripts/run_reproduction.py
```

Fresh calculations write to a new directory. Frozen evidence is retained; see docs/NUMERICAL_METHODS.md.

Boundary: 两个驱动位置的重合标记无法分辨多重性；没有把其余长时间曲线和密度像素比较自动判为完成。
