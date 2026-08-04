# Runnable code for prlb-f37350e-010

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/prlb-f37350e-010/code
python scripts/verify_public_artifacts.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Frozen non-final target states: T_BM_TAB1=blocked_missing_parameter, T_BM_TAB2=blocked_missing_parameter. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.
