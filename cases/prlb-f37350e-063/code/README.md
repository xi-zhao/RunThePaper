# Runnable code for prlb-f37350e-063

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/prlb-f37350e-063/code
python scripts/render_fast_formula_targets.py
python scripts/render_dynamic_targets.py
python scripts/render_cep_targets.py
python scripts/render_phase_diagram_targets.py
```

## Full paper-scale rerun

The implemented local campaign takes a few minutes and peaks near 2.2 GiB during the dynamic stage. It recomputes the published independent arrays and figures, but it does not close the four explicitly deferred paper items.

```bash
cd cases/prlb-f37350e-063/code
python scripts/run_fast_formula_targets.py
python scripts/run_dynamic_targets.py
python scripts/run_cep_targets.py
python scripts/run_phase_diagram_targets.py
python scripts/render_fast_formula_targets.py
python scripts/render_dynamic_targets.py
python scripts/render_cep_targets.py
python scripts/render_phase_diagram_targets.py
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: This is an in-progress partial full-paper reproduction. The paper-resolution Fig. 3(a) boundary, Fig. 4(a) fine multistable stripes, Fig. 4(d) five-attractor hierarchy, and Supplemental Fig. S2(b) 300-trajectory ensemble remain deferred; not every target has final isolated-run and independent-review evidence.
