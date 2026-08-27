# Runnable code for 1903.05124

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1903.05124/code
python scripts/run_reproduction.py --config config/isolation_smoke.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: All 44 visible theory-numerical panels and insets are frozen in the reproduction scope. Nine schematic panels and one numerical summary table are inventoried but excluded from figure generation. Source figures are comparison-only; every generated value must come from formulas or an independent Clifford/stabilizer computation. T001 now has a feature-scale reproduction of all four Main Fig. 2 numerical panels; paper geometry is preserved while sampling and finite-size grids remain reduced and explicitly labeled. T004 now has all ten Supplement Fig. S4 numerical items from a fresh EQC007 half-chain fit over independent generated observations; every scientific check passes at feature scale. T005 now has all seven Supplement Fig. S5 panels from 4,352 independent periodic-chain trajectories; critical points pass, while exponent-depth stability remains partial at L<=24 and eight realizations per cell. T006 now has all three Supplement Fig. S6 panels from 2,880 independent trajectories over every paper block size at exact d/m=3; all frozen scientific checks pass at feature scale, with sizes limited to L<=24. All 44 theory-numerical items now have independent formula-based evidence; 20 are paper scale and 24 are explicitly feature scale.
