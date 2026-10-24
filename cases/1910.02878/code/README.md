# Runnable code for 1910.02878

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1910.02878/code/requirements.txt
cd cases/1910.02878/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: TII 的一般矩阵/对称类证明范围仍未决；本案例不把受限引理提升为完整物理定理。
