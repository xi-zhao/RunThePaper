# Runnable code for 2402.14814

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2402.14814/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Experimental samples are not digitized and are recorded as missing_author_data. Supplement Fig. S2 uses a runnable reconstructed interaction model because the paper omits the complete coupled-channel and drive calibration inputs.
