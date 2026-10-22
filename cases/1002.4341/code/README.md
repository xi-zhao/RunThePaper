# Runnable code for 1002.4341

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1002.4341/code/requirements.txt
cd cases/1002.4341/code
python scripts/run_reproduction.py
```

Fresh calculations write to a new directory. Frozen evidence is retained; see docs/NUMERICAL_METHODS.md.

Boundary: 三模完整源曲线、正文0.28与源图0.4522尚未统一；源条件收敛g2(0)=0.34699064724。线宽、驱动、截断和有限制备时间控制均未恢复整条曲线。；原正Gaussian曲线和高于已受控占据范围的原条件计算仍未完成；625点热图已经完成，不重复计作待做。
