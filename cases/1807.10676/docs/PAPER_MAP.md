# Paper Map

## Identity

- Paper ID: `1807.10676`
- Title: *All "Magic Angles" Are "Stable" Topological*
- Authors: Zhida Song, Zhijun Wang, Wujun Shi, Gang Li, Chen Fang, B. Andrei Bernevig
- Publication: *Physical Review Letters* **123**, 036401 (2019)
- DOI: `10.1103/PhysRevLett.123.036401`
- Source: arXiv v2 PDF and TeX source bundle
- PDF SHA-256: `5bf7ff221ca2d543a08bf9909aeca0409e62b514c6d2bb40508f82e1375477fd`
- Source bundle SHA-256: `ae711f72fbb895dd3a9dabb3fc866dafe956ed902bd869ec3dba0725ad10c561`

## Reproduction goal

Re-derive and independently compute every feasible numerical panel in the main paper and embedded supplement. All continuum, Wilson-loop, tight-binding, node, and Wannier panels have been executed. The multi-terabyte/multi-day VASP campaign is now code-ready with deterministic decks and acceptance, while its licensed external run remains deferred; schematics and analytical representation tables are classified but not redrawn.

## Scientific structure

| Section | Role | Reproduction consequence |
| --- | --- | --- |
| Main topology argument | Relates isolated two-band irreps and Wilson winding | Compute isolation and four Wilson spectra |
| MBM supplement | Defines continuum Hamiltonian, phase evolution, nodes, and PH breaking | Compute all numerical panels in Supplement Figs. 2-7 |
| TB4-1V | Short-range model with matching topology | Compute bands and Wilson loop |
| TB8-2V / TB4-2V | Intervalley gap and Wannierizable effective models | Compute bands, Wilson loop, projected density |
| DFT appendix | Up to 11164-atom VASP validation | Execute D001-D012 through the code-ready paper-scale contract when licensed assets and quota exist |

## Equation inventory

| ID | Source | Role | Gate |
| --- | --- | --- | --- |
| EQ001 | Eq. (M-model-1) | Dimensionless MBM | verified |
| EQ002 | q/T definitions | Momentum honeycomb | verified |
| EQ003 | Main Fig. 1 caption | Velocity/gap/magic criteria | verified |
| EQ004 | Eq. (Wilson) | Wilson winding | verified |
| EQ005 | Eqs. (HTT-noPH), (HBB-noPH) | PH breaking | verified with one printed-label discrepancy |
| EQ006 | TB4-1V equations | Four-band lattice model | verified |
| EQ007 | Eq. (TB8-2V) | Intervalley model | verified |
| EQ008 | Projection/Wannier equations | Localized density | verified |
| EQ009 | Eq. (TB4-2V) | Effective two-valley bands | verified |

## Figure and table inventory

The authoritative per-panel decisions are in `figure_coverage.json`. It records 42 locally executed numerical subpanels in 12 composite targets, plus 12 DFT numerical entries whose shared implementation is code-ready but whose scientific outputs remain `deferred_blocked` for external compute/license requirements. Every non-numerical schematic/table is excluded with a reason.

## Assumptions and source repairs

- A complete hexagonal reciprocal cutoff is the physically symmetric truncation of the infinite MBM graph.
- The repeated `delta_2` label in the TB4 nearest-neighbour list is an evident TeX typo; the third C3-related vector is uniquely fixed.
- The second `2c` Wannier trial orbital uses the symmetry-related conjugation order; this is validated by the paper's independent `det S(k)` interval.
- The second PH-breaking top-row angle evaluates to `1.029°`; the figure prints `1.039°`. The computed formula is retained and the discrepancy is documented.
- Source figures and source TeX contain no allowed numerical arrays. No author code or plotted coordinates were used by the solver.
