# Numerical Methods

| Method | Targets | Scale | Main checks |
| --- | --- | --- | --- |
| NUM001 pseudospin evaluation | T001 | 121-point y grid; 151×151 winding cell | winding, nonzero field magnitude |
| NUM002 two-band bands | T002, T005 | cutoff 4, 41 points/segment | cutoff 5 comparison, symmetry |
| NUM003 DOS | T003 | 25×25 MBZ, top four bands, 0.12 meV Gaussian, two valleys | filling 0-8, finite/nonnegative DOS |
| NUM004 Berry/Chern | T004 | cutoff 4, 31×31 display and 21×21 integration | Chern signs/magnitude |
| NUM005 angle/bias sweep | T006-T007 | cutoff 4, 21 theta values, 9×9/7×7 k grids | two printed transition neighborhoods |
| NUM006 massive Dirac | T008-T009 | four states/G, cutoff 3, 31 points/segment | cutoff 4 comparison, Hermiticity |
| NUM007 spin mixing | T010-T011 | four states/G, cutoff 3, 31 points/segment | Hermiticity and two-band continuity |
| NUM008 paper-scale continuum campaign | T003, T006-T007 | 203 restartable conditions; cutoff 5/6; 101x101 DOS; 101-angle sweep | exact resume, DOS normalization, eigensolver residual, cutoff/grid convergence |

All eigensystems are small dense Hermitian matrices (maximum 244×244 in the convergence check). CPU execution is faster and simpler to attest than dispatching these matrices to the A100. The A100 remains available but would not remove the DFT workflow bottleneck.

Data are stored as compressed NumPy arrays with explicit units in field names. Every file is hashed before the render process starts.

Numerical risks are finite reciprocal cutoff, finite momentum grids, Gaussian DOS broadening and transition interpolation. None is hidden: cutoff/grid settings are in `config/paper_exact.json`, and convergence/transition errors are reported separately from visual similarity.

`config/paper_scale.json` makes the higher-resolution choices explicit.  They
are reconstructed numerical controls because the paper does not publish the
exact grids or broadening; executing them cannot by itself promote these
targets to `paper_exact`.
