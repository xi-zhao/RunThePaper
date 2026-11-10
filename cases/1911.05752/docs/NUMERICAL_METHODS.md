# Rerun / 复算

Validate the truncated likelihood mass by quadrature and use exact multinomial enumeration for the resampling control. The bundled independent simulator uses the stated protocol and new PCG64 seeds.

Use Python 3.13 and the [code instructions](../code/README.md). The entry point runs the following stages into a fresh directory.

- `core_controls.py`
- `resampling_control.py`
- `nmqa_simulation.py --panel F2c --protocol paper --repeats 2 --output results/f2c-short.npz`

The overview is drawn from the recorded independent outputs. [Curve data](../outputs/data/overview.json) · [Scientific assessment](../outputs/checks/completion_assessment.json)
