# Method Trace

| Scientific step | Paper basis | Independent implementation | Evidence |
| --- | --- | --- | --- |
| Fixed-particle Hilbert space | Eq. (1), half filling | bit-state enumeration | `src/mbl_level_stats/hamiltonian.py` |
| Fermionic Hamiltonian | Eq. (1) | signed nearest/next-nearest hopping plus diagonal interaction/disorder | unit tests and `CHK_HERMITIAN` |
| Conditioned Gaussian disorder | paragraph after Eq. (1) | per-sample exact RMS normalization | unit tests and frozen config |
| Full-spectrum statistic | Eqs. (2)-(3) | dense symmetric eigensolve and all interior ratios | `statistics.py`, `science_checks.json` |
| Disorder curves and crossings | Main Fig. 2 discussion | streaming sample aggregate plus explicit sign-change/nearest-approach logic | `campaign.py`, generated CSVs |
| Presentation | printed figures only | post-freeze RenderContract | `config/render_contract.json`, `render_manifest.json` |

The scientific runner is isolated from `raw/` and reference-image directories.
Original figures are accessed only after generated arrays are frozen, and only
for layout/style comparison.  The RenderContract cannot change parameters or
scientific arrays; before/after hashes are identical.
