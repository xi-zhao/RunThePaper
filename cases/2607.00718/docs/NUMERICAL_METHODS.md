# Numerical Methods

- Closed-form targets use vectorized NumPy evaluation at the paper grids.
- Time-domain targets propagate the exact affine first/second-moment system by
  fixed-size matrix evolution and cross-check it with an independent Gaussian
  master-equation solver.
- Passive energy and ergotropy use the single-mode symplectic invariant of the
  centered covariance.
- The S1 cutoff audit uses a separately isolated finite-Fock Liouvillian. It is
  diagnostic evidence, not the production generator.
- Every run writes structured data before rendering a figure.
- CC BY 4.0 author arrays are loaded only after generation for numerical
  comparison. Paper pixels and digitized curves are never generation inputs.

Run a target from the public case directory with:

```bash
python code/scripts/run_target.py T002A
python code/scripts/run_target.py TS01
```

The optional Torch-based cutoff probe can be rerun with:

```bash
python code/scripts/run_target.py TS01 --mode truncation-probe
```
