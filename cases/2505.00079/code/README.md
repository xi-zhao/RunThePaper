# Runnable code for 2505.00079

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install torch
cd cases/2505.00079/code
python scripts/verify_public_artifacts.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Frozen non-final target states: T001=partially_reproduced, T002=partially_reproduced, T003=partially_reproduced, T004=failed, T005=partially_reproduced, T006=blocked_compute_scale, T007=blocked_compute_scale, T008=blocked_compute_scale. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.
