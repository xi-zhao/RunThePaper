# Derivation Trace

| Formula | Paper source | Code path | Independent evidence |
| --- | --- | --- | --- |
| EQ012 basis | Eq. (1) | `_operator`, `continuum_hamiltonian` | continuum basis tests |
| EQ001 intrinsic Dirac mass | Eqs. (2)-(3) | `continuum_hamiltonian` | direct eigenspectrum |
| EQ002 continuum Rashba | Eq. (4) | `continuum_hamiltonian` | four ratio gap sweep |
| EQ003 spin Hall topology | Eq. (5) and Kubo prose | `honeycomb_bulk_hamiltonian`, `fukui_chern_number` | periodic Berry-flux sum |
| EQ004 lattice model | Eq. (6), Fig. 1 | zigzag/armchair geometry and ribbon solvers | width, endpoint, localization and DOS checks |
| EQ009 lattice Rashba | p. 3 Rashba prose | `spinful_ribbon_hamiltonian`, `bulk_half_filling_gap_edges`, `rashba_edge_spectral_flow` | full-BZ branch tracking, independent bulk-gap selection, exact uniform baseline, both orientations and three widths |
| EQ010 S constraint | p. 3 disorder prose | `time_reversal_scattering_basis`, `helical_scalar_disorder_ensemble` | SVD null space plus 32 random profiles |
| EQ011 interaction operator | p. 3 interaction prose | `interaction_operator_diagnostics`, `interaction_conductivity_sweep` | field/derivative counting and independent log-log fits |
| EQ005 transport | Fig. 2 and prose | transmission tensor and LB solver | explicit terminal currents |
| EQ006 bare gap | Eq. (7) and first-star prose | `first_star_projection_diagnostics`, `bare_gap_kelvin` | explicit 8x8 projection plus dimensional SI evaluation |
| EQ007 field Rashba | p. 4 field prose | `rashba_kelvin` | dimensional SI evaluation |
| EQ008 Coulomb RG | Eq. (8) and integrated equation | shell integration plus RG running/root solvers | independently derived coefficients, ODE residual and self-consistency |
| EQ013 first-star matrix | Eq. (7), first-star prose | `first_star_spin_orbit_matrix` | full matrix versus Pauli-product identity |
| EQ014 finite-Rashba response proxy | prose after Eq. (5) | `conventional_spin_hall_sweep` | full-BZ conventional-current Kubo sweep; exact cited current remains unavailable |
| EQ015 one-loop shell integrals | Fig. 3, Eq. (8) | `derive_one_loop_flow_coefficients`, `exchange_log_sweep` | matrix projection and shell-width linearity |
| EQ016 RPA screening | screening prose before Eq. (8) | `neutral_graphene_polarization`, `screened_coulomb_diagnostics` | interband integral, angular/cutoff convergence and downstream power fit |
| EQ017 broken-T proxy and edge field | p. 3 parallel-field prose | `dirac_mass_symmetry_inventory`, `parallel_field_mass_path`, `translation_preserving_parallel_field_path` | exhaustive Pauli search, direct edge gap, translation diagnosis and continuous-optimizer falsification of the minimal published-term bulk path |
| EQ018 cylinder spectral flow | Laughlin paragraph | `cylinder_flux_spectral_flow` | explicit level permutation across one flux quantum |

The machine-readable source traces, check statuses and code references are in
`EQUATION_CARDS.json`; `outputs/checks/formula_verification.json` is generated
from that single source of truth.
