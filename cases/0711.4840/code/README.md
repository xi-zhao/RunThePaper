# Runnable code for 0711.4840

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/0711.4840/code/requirements.txt
cd cases/0711.4840/code
python scripts/run_reproduction.py
```

Fresh calculations write to a new directory. Frozen evidence is retained; see docs/NUMERICAL_METHODS.md.

Boundary: 同批记录的RMS区间汇总恢复三组p20，平均区间则给10/16/16；需继续核对完整插图数值与统计口径，不把候选RMS准则说成作者已确认方法。主图原始圆点比较已修正并保留。
