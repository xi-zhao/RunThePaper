# Runnable code for 10.1038-s41586-026-10720-3

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install torch
cd cases/10.1038-s41586-026-10720-3/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: The measured fibre dispersion coefficients, fitted frame corrections, six Fig. 4 parameter tables, raw spectra, raw fluxes, and measured pulse states are unavailable. The 47-unit paper profile is code-ready; a 17-unit CPU smoke profile completed with isolated file-access attestation. The formula-only PCF surrogate does not recover the printed 1551 nm horizon, so it is recorded as a missing-parameter/model-mismatch boundary rather than a paper error. Historical vector-trace fits, marker regressions, pixel scores, and UPPE outputs based on the traced dispersion are retained only as comparison history and are ineligible as scientific evidence. No author scientific code, author numerical arrays, digitized curves, or source pixels enter the formula-only numerical runner. The public projection and publish manifest have not yet been refreshed from this calibration state.
