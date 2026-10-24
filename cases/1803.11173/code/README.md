# Runnable code for 1803.11173

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1803.11173/code/requirements.txt
cd cases/1803.11173/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Fig3/Fig4 原始采样层级 m、重抽规则和深度法则缺失，两项源值检查保持外部资源受阻。
