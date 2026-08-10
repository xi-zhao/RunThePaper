# Method Trace

## NUM001 — T001 lattice calculation

- Inputs: `L=10000`, half filling, printed Toeplitz kernel.
- Steps: construct Toeplitz matrix; solve 96 central eigenvalues; convolve charge and entropy weights.
- Outputs: `fig2_charge_resolved.csv`, `single_particle_spectrum.csv`.
- Checks: edge saturation, particle-hole symmetry, probability normalization, entropy sum, charge symmetry.
- Status: verified.

## NUM002 — T002 spectrum calculation

- Inputs: accepted EQ001 eigenvalues, 24 closest-to-zero entanglement energies.
- Steps: enumerate `2^24` many-body weights; label charges; rank each sector; evaluate Eq. (11) by quadrature.
- Outputs: `fig3_spectrum_numeric.csv`, `fig3_spectrum_analytic.csv`.
- Checks: 24-mode count, monotone sector onsets, all-sector `I0` identity.
- Status: verified.

## NUM003 — code-ready rerun orchestration

- Inputs: formula-derived config only; the historical CSV hashes are audit
  metadata and never numerical inputs.
- Steps: checkpoint shared eigenvalues; checkpoint the T001 recurrence;
  partition the exact T002 integer state domain and analytic x grid; validate
  shard identities; aggregate; benchmark two backends; evaluate per-target
  acceptance.
- Mathematical equivalence: the global top-k set must be contained in the union
  of each shard's local top-k set. Selecting the global top-k from that union is
  therefore identical to monolithic enumeration for the plotted rank window.
- Outputs: `outputs/paper_scale/**` for paper profile and
  `outputs/paper_scale_smoke/**` for exploratory validation.
- Checks: config-load, interruption/resume, exactly-once shard coverage,
  streaming/monolithic parity, backend parity, convergence and invariants.
- Status: code-ready; CPU smoke passed. Historical paper-exact outputs were not
  rerun.

## CLAIM001 — unplotted Ising verification statement

- The paper prints the formula but omits every claim-relevant numerical setup
  choice and any numerical artifact.
- The executable lane checks formula normalization and scaling only.
- Status: formula sanity passed; authors' numerical verification remains
  unavailable, not paper-exact.

## RENDER001 — post-run RenderContract

- Inputs: only the three SHA-256-locked CSV files.
- Source figures: accessible only after attested numerics, for canvas, axes, typography, color, markers and legend layout.
- Forbidden changes: physics parameters, sector identities, numerical values and arrays.
- Outputs: high-resolution PNG plus editable SVG/PDF and comparison boards.
- Status: passed.
