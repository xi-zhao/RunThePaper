# Runnable code for 1810.05651

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1810.05651/code
python scripts/verify_public_artifacts.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: The legacy case has no machine-verifiable author-code isolation attestation. The statistical reproduction consumes released experimental count data; it is not a first-principles simulation of the hardware experiment. No source-image comparison panel or digitized source curve is published in this projection.
