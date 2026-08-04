# Method trace — single-link Metropolis Monte Carlo

## MTH001: paper kernel

- Source: supplementary “Details of simulations.”
- State: one Z_N integer per directed positive link on a periodic L^4 torus.
- Proposal: choose a trial link value uniformly from Z_N, including the current
  value.
- Acceptance: `min(1, exp(-Delta S))` from incident plaquettes and, when
  `mu != 0`, incident cubes.
- Sweep: update every link once.
- Measurements: paper-specific skipped sweeps from SM Table 1.

## MTH002: exact coloured implementation

The baseline groups links that share no action term. Wilson/Z4 runs use two
parity colours per direction; monopole-suppressed runs use eight transverse
parity colours per direction so no same-colour links share a cube. Within one
colour, simultaneous accept/reject decisions are identical to an arbitrary
sequential order because their local actions are independent.

Checks:

- partition and cube non-overlap of monopole colour masks;
- local Delta S versus brute-force total-action difference for all three models;
- deterministic chains for fixed seed;
- bounded Polyakov/defect observables;
- even-L guard for periodic colouring.

## MTH003: histogram symmetry convention

The supplement states that Polyakov data are augmented by every Z_N rotation.
`symmetry_augment_polyakov` implements the full orbit. It preserves every
radius and drives the augmented complex mean to zero. Both raw and augmented Q
are reported because only the latter follows the plot convention.

## MTH004: uncertainty and thermalization

The source describes binned jackknife saturation and bootstrap errors but does
not give thermalization length. Final runs must:

1. run hot/cold convergence pilots;
2. record the chosen burn-in;
3. save raw time series and acceptance rates;
4. quantify integrated autocorrelation or bin-error plateaus;
5. use bootstrap/jackknife errors matching the paper item.

Current smoke outputs are diagnostic and cannot satisfy MTH004.
