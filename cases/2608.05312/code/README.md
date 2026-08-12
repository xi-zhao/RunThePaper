# Runnable code for 2608.05312

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2608.05312/code
python scripts/run_checks.py
python scripts/run_reproduction.py --profile quick --targets all --output-root ../outputs/quick
```

## Declared paper-parameter-subset rerun

The paper-subset profile uses the paper's printed system sizes and rates, 15 to 20 disorder realizations for the main targets, paired seeds, adaptive log-rate scans, and a reduced five-realization 9x9 N=64 temperature map. The committed formal run took roughly eleven minutes on a 16 GiB Apple M4.

```bash
cd cases/2608.05312/code
python scripts/run_reproduction.py --profile paper_subset --targets all --output-root ../outputs/paper_subset
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: This is not an author-data-level or paper-exact reproduction. The paper omits the mean hopping, exact source-state notation, author random seeds, and exact scan grids, so the results remain paper_subset. The N=64 temperature map uses five realizations on a 9x9 grid. The QCLE figure is blocked because the lead/bath matrices, chemical potentials, initial state, and runnable author implementation are not supplied.
