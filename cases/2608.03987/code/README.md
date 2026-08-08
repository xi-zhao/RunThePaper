# Runnable code for 2608.03987

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install cotengra==0.7.5 opt_einsum==3.4.0
cd cases/2608.03987/code
python scripts/fetch_benchmark_inputs.py
python scripts/run_independent_reimplementation.py --preset smoke --scope random --circuit test
```

## Full clean-room 67-circuit rerun

The full preset fixes seed 42, ten generic cotengra candidates, 600,000 NNI steps per objective, and 60,000 polish steps. The completed records sum to about 29.3 CPU-minutes; parallel wall time depends on how the circuit set is sharded.

```bash
cd cases/2608.03987/code
python scripts/run_independent_reimplementation.py --preset full --output-dir ../outputs/data/independent_python_full
python scripts/run_reproduction.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: This is not a complete reproduction of the paper. The independent optimizer differs from the published optimizer and reproduces only 58/67 Figure-9 threshold labels. The package evaluates contraction-tree arithmetic, not Ascend 910/A800 tensor kernels, so it does not reproduce device wall clocks, precision, or end-to-end acceleration tables. The official Zenodo ZIP is downloaded separately; the primary optimizer opens only its 122 raw circuit and observable payloads, while author results are used only for post-hoc comparison.
