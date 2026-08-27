# Runnable code for 2510.12880

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2510.12880/code
python scripts/run_reproduction.py --target T001
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: All 25 first-excited values agree with the digitized source within 0.0015. The ground-state panel has one retained 0.00364 discrepancy at theta=10 degrees, N=12; the remaining 24 values agree within 0.0015. The paper omits eigensolver and tolerance details, so the two rendered overlap artifacts remain exploratory despite their strong numerical agreement. The full-paper item audit finds 9 eligible scientific items: 4 covered and 5 uncovered, for 44.44% coverage and reproduction degree 40.90. V003-V007 expose three open-chain results, one parity-selection rule, and one perturbative-sector claim that still lack independent implementations.
