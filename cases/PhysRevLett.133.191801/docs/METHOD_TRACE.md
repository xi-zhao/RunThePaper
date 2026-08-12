# Method trace

## METHOD001 -- linear-response propagation

- Source: main Eqs. (2)--(4).
- Inputs: declared time grid, source drive, resonance, coherence time, gain.
- Algorithm: exact exponential update for a linearly interpolated drive.
- Independent check: fourth-order Runge--Kutta integration.
- Outputs: response arrays for T001--T003.
- Code: `src/axion_spin/transfer.py`, `src/axion_spin/signals.py`.

## METHOD002 -- optimal filtering

- Source: main Eq. (5).
- Inputs: signal template, sensor record, optional PSD.
- Algorithm: normalized frequency-domain correlation.
- Independent check: direct time-domain least-squares estimate at a known lag.
- Feature evidence: deterministic seeded synthetic injection/noise only.
- Paper-scale boundary: measured PSD and 60-second records are required.
- Code: `src/axion_spin/filtering.py`, `src/axion_spin/experimental.py`.

## METHOD003 -- statistical aggregation

- Source: Fig. 4(a) text and reported uncertainties.
- Inputs: per-dataset estimates and independent error components.
- Algorithm: Gaussian likelihood summary and quadrature propagation.
- Feature evidence: printed aggregate values only, not the 36 unavailable
  estimates.
- Code: `src/axion_spin/statistics.py`.

## METHOD004 -- coupling conversion

- Source: main Eq. (1) and printed 4.94 micro-eV constraint.
- Inputs: mass, source-sensor geometry, spin orientations, measured field bound.
- Algorithm: point-source tensor kernel for the feature lane; paired Sobol
  finite-volume quadrature for the paper-scale lane.
- Paper-scale boundary: exact cell geometry and polarization model are required.
- Code: `src/axion_spin/axion.py`, `src/axion_spin/paper_scale.py`.
