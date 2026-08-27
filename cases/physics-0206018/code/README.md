# Runnable code for physics-0206018

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/physics-0206018/code
python scripts/run_reproduction.py --config config/feature.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: The attested production run uses the published N=1600 scale and passes the paper-declared rounding/discretization equivalence contract. The prose and Figure 4 disagree on the vertical displacement sign, so the figure-defined publication variant is paper_subset pending fresh review. Original figures are used only after numerical artifacts are frozen, for RenderContract and diagnostic comparison.
