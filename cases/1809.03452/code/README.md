# Runnable code for 1809.03452

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1809.03452/code/requirements.txt
cd cases/1809.03452/code
python scripts/run_reproduction.py
```

Runs the listed independent stages into a fresh directory. See docs/NUMERICAL_METHODS.md.

Boundary: 历史实机配置未公开。公开入口重算 10 μs 方波基准和 Bell 对照，论文矢量点与 Qobj 原样文件保留原来源。
