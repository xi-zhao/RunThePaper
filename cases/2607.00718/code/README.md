# Runnable code for 2607.00718

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install torch (optional, only for the TS01 truncation probe)
cd cases/2607.00718/code
python scripts/run_target.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Figure 1(c) leaves the absolute representative squeezing unspecified. The released Figure 4 transmission arrays belong to an earlier manuscript and peak at 10.07 rather than the final-formula 27.31. Figure S1 does not disclose its finite-Hilbert cutoff or convergence study. Figure S3 has no released array and its printed axis conflicts with the visible unit intercepts, so author confirmation remains open. Scientific visual fidelity is 90.31; the secondary presentation diagnostic is 66.23 and contributes no scientific credit.
