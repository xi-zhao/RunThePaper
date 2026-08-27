# Target Ledger

| Target | Atomic scientific object | Primary gate | Parameter status |
| --- | --- | --- | --- |
| T001 | Fig. 1 zigzag bands, both edge orientations, localization, full flat-band interval and DOS | SCI_BULK_GAP; SCI_ZERO_T2_FLAT_EDGE_BAND; SCI_ARMCHAIR_KRAMERS_CROSSING | paper subset |
| T002 | continuum Dirac spectrum and intrinsic gap | SCI_CONTINUUM_INTRINSIC_GAP | paper exact |
| T003 | continuum/lattice Rashba boundary and conventional-current Kubo proxy | SCI_RASHBA_FULL_K_EDGE_SPECTRAL_FLOW; SCI_RASHBA_KUBO_PROXY | boundary feature supported across full BZ/two orientations/three widths; exact finite-Rashba current definition unavailable |
| T004 | spin Chern response, symmetric-mass inventory, edge Zeeman gap, generic broken-T proxy and minimal-path falsification | SCI_SPIN_CHERN_PAIR; SCI_DIRAC_MASS_SYMMETRY_ENUMERATION; SCI_PARALLEL_FIELD_EDGE_GAP; SCI_TR_BROKEN_INTERVALLEY_MASS_PATH_PROXY; SCI_PARALLEL_FIELD_MINIMAL_PATH_FALSIFICATION | topology/symmetry and edge gap supported; paper's connecting bulk terms are publication-underspecified |
| T005 | h/e flux pump and finite-cylinder spectral flow | SCI_FLUX_PUMP; SCI_FINITE_CYLINDER_SPECTRAL_FLOW | paper exact invariant; finite grid reconstructed |
| T006 | Kramers protection and random scalar-disorder ensemble | SCI_NO_ELASTIC_BACKSCATTER; SCI_RANDOM_TR_DISORDER_ENSEMBLE | paper exact model; sampling reconstructed |
| T007 | allowed interaction operator, dimension and `u,T` conductivity exponents | SCI_INTERACTION_OPERATOR; SCI_INTERACTION_CONDUCTIVITY_SWEEP | paper exact formula; sampling reconstructed |
| T008 | Fig. 2(a) charge conductance | SCI_TWO_TERMINAL_TRANSPORT | paper exact |
| T009 | Fig. 2(b) spin current | SCI_FOUR_TERMINAL_SPIN_TRANSPORT | paper exact |
| T010 | explicit first-star matrix and intrinsic-SO estimate | SCI_FIRST_STAR_PROJECTION; SCI_BARE_GAP_ESTIMATE | matrix paper exact; paper's rounded scale lacks the lattice constant used for a decimal reconstruction |
| T011 | electric-field Rashba estimate | SCI_RASHBA_ESTIMATE | formula paper exact; paper's rounded scale lacks the Fermi velocity used for a decimal reconstruction |
| T012 | one-loop shell coefficients, screening and integrated flow | SCI_RG_FLOW; SCI_RG_EXCHANGE_LOG; SCI_NEUTRAL_GRAPHENE_SCREENING | equations paper exact; quadrature reconstructed |
| T013 | self-consistent enhanced full gap | SCI_RG_GAP | paper exact |

All 13 targets share the isolated run
`cond-mat-0411737-whole-paper-v12`.  All scientific arrays are generated before
rendering; only T001 has a numerical source panel and therefore a pixel target.
The target ledger never upgrades the declared conventional-current Kubo proxy
to the paper's unprinted conserved-current observable.
