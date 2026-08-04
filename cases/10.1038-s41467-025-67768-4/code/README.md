# Runnable code for 10.1038-s41467-025-67768-4

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/10.1038-s41467-025-67768-4/code
python scripts/verify_public_artifacts.py
```

## Independent numerical rerun

This command recomputes the scientific numerical arrays from the public equation-based implementation. It does not read a paper image, digitized source curve, or author numerical code; runtime varies from seconds to CPU minutes.

```bash
cd cases/10.1038-s41467-025-67768-4/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Frozen non-final target states: T001=failed, T002=partially_reproduced, T003=partially_reproduced, T004=partially_reproduced, T005=partially_reproduced, T007=partially_reproduced, T008=blocked_missing_method, T009=blocked_missing_method. No source-image comparison panel or digitized source curve is published in this projection.
