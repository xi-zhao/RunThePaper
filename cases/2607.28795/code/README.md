# Runnable code for 2607.28795

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2607.28795/code
python scripts/run_reproduction.py --config config/run_parameters.json --paper-inputs config/paper_inputs.json --group-tables config/group_tables.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: artifact_integrity=artifact_valid_with_warnings, parameters=mixed, causal_resolution=repair_required, science=failed, pixel=not_comparable, paper_assessment=inconclusive.
