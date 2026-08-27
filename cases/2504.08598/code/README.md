# Runnable code for 2504.08598

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2504.08598/code
python scripts/run_reproduction.py --config config/clean_room_reproduction.json --output-root outputs/public_quick_run
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Figure 8 curve E/F and distribution E, and Figure 9 distribution H remain named mismatches. Pasqal/Pulser qubit validation is not applicable to the multilevel qudit Hamiltonian; no real hardware or advantage claim.
