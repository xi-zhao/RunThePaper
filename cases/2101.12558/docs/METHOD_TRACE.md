# Method Trace

| Method | Input | Output | Implementation | Status |
| --- | --- | --- | --- | --- |
| NUM001 slab/QE | printed slab scalars | deterministic QE decks | `structure.py`, `qe.py` | reconstructed coordinates |
| NUM002 Wannier/Dyson | public `*_hr.dat`, printed layer symmetry | local Green/Weiss fields | `qe.py`, `self_consistency.py` | streaming fixed point verified |
| NUM003 CT-HYB/self-consistency | layer Weiss fields, U/J | chain-averaged self-energies, direct orbital chi, density correction and charge fixed point | `cthyb.py`, `self_consistency.py`, paper runner | scientific core code ready; public backend/input deferred |
| NUM004 observables | frozen Green/self-energy | MaxEnt/Pade spectra, layer/k projections and chi | `maxent.py`, `observables.py`, `paper_scale.py` | independent continuation tested; paper scale deferred |
