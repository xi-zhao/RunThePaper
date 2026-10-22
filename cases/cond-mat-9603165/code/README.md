# Runnable code for cond-mat-9603165

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/cond-mat-9603165/code/requirements.txt
cd cases/cond-mat-9603165/code
python scripts/run_reproduction.py
```

Fresh calculations write to a new directory. Frozen evidence is retained; see docs/NUMERICAL_METHODS.md.

Boundary: 空间宽度原坐标定义下，原尺度100组无序集合支持余差统计相容；新诊断尚未更新原始对象验收，需保持完整来源对照的明确口径。作者精确种子或代码身份不作为额外完成要求。
