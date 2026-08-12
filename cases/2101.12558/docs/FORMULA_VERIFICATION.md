# Formula Verification

Nine formula cards trace the full chain from Wannier projection through
Dyson/DMFT, CT-HYB, charge feedback, spectra, spin correlations, and surface
energy. All numeric gates are open. “Open” means the equation is traceable and
implemented; it does not mean the material calculation ran.

Machine record: `outputs/checks/formula_verification.json`.

| Formula group | Gate | Remaining production uncertainty |
| --- | --- | --- |
| H(KS), lattice/local Dyson | open | exact projector gauge and k mesh |
| CT-HYB, U/J, FLL | open | sampling controls and full occupancy history |
| charge feedback | open | unpublished adapter/mixing convention |
| spectra/continuation | open | MaxEnt model/covariance and broadening |
| chi(tau), surface energy | open | estimator binning and full-precision energies |
