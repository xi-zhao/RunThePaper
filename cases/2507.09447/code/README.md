# Runnable code for 2507.09447

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2507.09447/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Paper-scale L=1000 x 3200-realization OBC/PBC diagonalization completed locally. All nine scientific gates pass; strict source-pixel SSIM >=0.95 does not pass. Formal Science Bulletin supplementary material is method evidence only; reproduction targets remain arXiv v1.
