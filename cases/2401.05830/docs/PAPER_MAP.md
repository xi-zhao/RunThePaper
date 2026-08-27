# Paper Map

## Identity

- Paper ID: `2401.05830`
- Title: *Inverse Mpemba Effect Demonstrated on a Single Trapped Ion Qubit*
- Authors: Shahaf Aharony Shapira, Yotam Shapira, Jovan Markov, Gianluca
  Teza, Nitzan Akerman, Oren Raz, and Roee Ozeri
- Preprint: arXiv:2401.05830v2 (12 May 2024)
- Publication: *Physical Review Letters* **133**, 010403 (2024)
- DOI: `10.1103/PhysRevLett.133.010403`
- Local PDF: `raw/arxiv-2401.05830v2.pdf`
- Local source: intentionally absent; the author source archive and any author
  numerical implementation are outside the permitted access boundary.

## Reproduction Goal

Independently derive the driven-qubit GKSL dynamics and reproduce every
formula-generated numerical panel in the main paper and Supplemental Material.
Where a panel mixes experimental samples with theory, only the independently
generated theory layer is in scope.  Raw tomography points, shot-noise bars,
polynomial-smoothed author data, and pulse-sequence oscillations are not
reconstructed from pixels or guessed arrays.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Main text, model | Defines the coherently driven qubit, decay/dephasing split, Bloch dynamics, steady-state locus, relaxation modes, and strong inverse Mpemba condition | Main Eqs. (1)-(4) |
| Main text, experiment | Implements the effective channel on a single trapped `88Sr+` ion | Experimental arrays are unavailable and excluded as numerical inputs |
| Main Figs. 2-5 | Theory/experiment evidence for the inverse effect | Theory layers in Figs. 2 and 4 are targets; experimental series remain explicit excluded inventory rows |
| Supplemental Sec. 1 | Derives the 4x4 Liouvillian, Bloch ODE, steady state, eigenmodes, and modal coefficients | Supplement Eqs. (1)-(11) |
| Supplemental Secs. 2-3 | Geometric proof excluding a strong direct effect and illustrating the inverse effect | Supplement Figs. 2-5 |
| Supplemental Sec. 4 | Binomial tomography error propagation | Not used without author measurement counts |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | Supplement Eqs. (1)-(2) | Figure-consistent GKSL generator | verified from source and operator identities |
| EQ002 | Supplement Eqs. (1)-(4) | Bloch-space affine ODE | verified by direct density-matrix expansion |
| EQ003 | Supplement Eqs. (5)-(8) | Steady state and ellipse locus | verified by residual and ellipse identity |
| EQ004 | Main Eq. (4), Supplement Eqs. (9)-(10) | Rates, modes, and bifurcation | verified by characteristic polynomial |
| EQ005 | Main strong-effect formula, Supplement Eq. (11) | Slow-mode coefficient and its zero | verified against independent mode annihilation |
| EQ006 | Main Eq. (3) | Exact affine propagation, distance, crossing time | verified against a 4x4 density-matrix Liouvillian |
| EQ007 | Supplemental text after Eq. (8) | Pure-state mixture used for direct preparation | verified from Bloch geometry |
| EQ008 | Main Eqs. (1)-(2) | Literal printed-rate falsification comparator | source-only; factor-two conflict with supplement retained for review |

## Figure/Table Inventory

| Item | Caption summary | Atomic items | Notes |
| --- | --- | --- | --- |
| Main Fig. 1 | Physical cartoon, levels, and pulse sequence | 3 schematic | excluded |
| Main Fig. 2 left | Three measured/fitted loci and the `alpha=0.94` temperature-colored locus | 3 theory + 3 experiment | theory T001; experiments excluded |
| Main Fig. 2 right | Slow-mode coefficient at `alpha=0.94`, `gamma_f'=15` | 1 theory | T002 |
| Main Fig. 3 top/bottom | Raw and polynomial-smoothed tomography distances | 2 experiment panels | excluded |
| Main Fig. 4 | Raw/smoothed distance difference plus two theory curves | 2 theory + 2 experiment | theory T003; experiments excluded |
| Main Fig. 5 main/inset | Direct-preparation tomography distances and their difference | 2 experiment | excluded |
| Supplement Fig. 1 | Real Liouvillian rates versus final temperature | 4 theory | T004 |
| Supplement Fig. 2 | Steady-state loci and both bifurcation branches | 7 theory | T005 |
| Supplement Fig. 3 | Fast-mode chords proving absence of strong direct ME | 2 theory | T006 |
| Supplement Fig. 4 left/right | Three relaxation trajectories and late-time mode zoom | 6 theory | T007/T008 |
| Supplement Fig. 5 left/right | Crossing time and maximal post-crossing separation | 2 theory | T009/T010 |
| Tables | none | not applicable | no tables appear in the paper or supplement |

Display inventory is complete at 39 atomic items. The denominator additionally includes two
independent no-display claims: T011 tests the main/supplement dissipator-rate normalization, and
T012 tests the prose/equation Hamiltonian normalization. Both are currently uncovered and are
enumerated separately so that the ten successful figure targets cannot hide them.

## Assumptions

- Set `Omega=1`; all temperatures are the printed dimensionless
  `gamma'=gamma/Omega` and plotted time units are converted explicitly.
- Use the printed fitted value `alpha=0.94` for the main strong-effect panels.
- Use the continuous GKSL model.  The experiment-only digitized Trotter
  oscillations cannot be recreated without the unprinted pulse-level channel.
- Original PDF pixels may be viewed only for inventory and post-freeze
  presentation comparison.  They never enter formulas, parameters, arrays, or
  numerical optimization.
