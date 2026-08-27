# Runnable code for 10.1103-PRXQuantum.6.010331

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/10.1103-PRXQuantum.6.010331/code
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Formal publication identity verified as PRX Quantum 6, 010331 (2025), DOI 10.1103/PRXQuantum.6.010331. Fig. 15 and Fig. 6(a) envelopes are reproduced from the paper-exact Appendix-L functions; those approximate fits omit small intensity side peaks, and the independent Hamiltonian diagnostic is reconstructed because the target-specific phase trajectory is not disclosed.
