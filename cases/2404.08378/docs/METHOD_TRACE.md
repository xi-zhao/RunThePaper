# Method Trace

## NUM001 — Exact two-mode quantum propagation

- Source: Main Eqs. (1)–(4), Supplement Eqs. (1)–(2).
- Inputs: phase, source balance, spectral-overlap parameter.
- Outputs: classical transfer rates and `{|20>,|11>,|02>}` probabilities.
- Method: construct the printed 2×2 MZI unitary, lift it analytically to the symmetric two-boson representation, then propagate a state vector or density matrix.
- Code: `src/lnoi_interference/quantum.py`.
- Checks: one- and two-photon unitarity, normalization, positivity, bunching/antibunching limits.
- Status: verified.

## NUM002 — Independent waveguide reconstruction

- Source: printed geometry around Main Fig. 1(c) and Supplement Fig. S7.
- Inputs: wavelengths, cross-section dimensions, declared refractive indices and electrode gaps.
- Outputs: normalized transverse intensities, effective indices, relative metal-overlap loss.
- Method: sparse scalar finite-difference Helmholtz eigenproblem plus perturbative modal overlap with the metal region.
- Code: `src/lnoi_interference/modes.py`.
- Checks: guided `n_eff`, unit intensity integral, loss decreasing with gap.
- Status: verified reconstruction; not vector-FEM paper-exact.

## NUM003 — HOM and metrology audit

- Source: Supplement Eqs. (3)–(4), Main Fig. 4 values, brightness paragraph.
- Inputs: splitter reflectivity, explicit spectrum approximation, dip visibility/width, coincidence rate, loss and pump power.
- Outputs: monochromatic/spectral HOM visibility, delay curve, bandwidth conventions and brightness.
- Method: exact coincidence-ratio functional, transparent quadrature, Gaussian line shape and direct unit-aware arithmetic.
- Code: `src/lnoi_interference/metrology.py`.
- Checks: HOM limits, spectrum ordering, half-maximum identity and independent brightness closure.
- Status: exact functional with declared partial inputs.

## NUM004 — Fail-closed experimental reanalysis

- Source: captions and axes for the nine experimental-array items.
- Inputs: eight explicitly named author CSV tables with strict schemas.
- Outputs: validation records and reanalysed observables only when every required table exists.
- Method: validate columns, units, ranges and uniqueness before any computation; abort otherwise.
- Code: `src/lnoi_interference/experimental.py`, `scripts/run_paper_scale.py`.
- Checks: missing-input inventory and no digitization/synthetic fallback.
- Status: code ready, blocked by missing author data rather than compute.
