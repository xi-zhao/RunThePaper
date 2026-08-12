# Method Trace

## METHOD001 — unfolded resonance statistics

- Inputs: interval mean count and normalized spacing grids
- Method: analytic Poisson/GOE references plus seeded random-matrix cross-check
- Outputs: T001–T002 curve tables
- Invariant: normalized spacing densities and unit mean spacing

## METHOD002 — independent atom-ion collision ensemble

- Inputs: printed masses, bath temperature, rf/secular frequencies, displacement fields
- Method: checkpointable 3D elastic COM collision map with random rf phase
- Outputs: T003 median energy and T004–T005 velocity distributions
- Invariants: per-collision momentum/energy conservation, stationary median,
  quadratic field response, radial/axial anisotropy
- Boundary: paper's Julia code and omitted microscopic MD inputs are not used

## METHOD003 — universal polarization capture

- Inputs: dimensionless collision energy and partial wave
- Method: complex ODE with incoming WKB short-range boundary and asymptotic
  Riccati-Hankel matching
- Outputs: capture probabilities for T007–T017
- Invariants: probability in `[0,1]`, `k^(2l+1)` threshold, p/d/f barriers at
  `1/9/36 E_s`, high-energy saturation

## METHOD004 — nonthermal recombination averaging

- Inputs: independent ion ensemble, two thermal Li velocities, density,
  printed/reconstructed resonance parameters
- Method: remove three-body COM velocity, evaluate the printed Lorentzian cross
  section, average rates, and apply exponential survival
- Outputs: T007–T016 spectra and energy trends
- Boundary: missing f-wave coupling and bare resonance position remain declared
  reconstruction parameters and cannot be fitted from source pixels
