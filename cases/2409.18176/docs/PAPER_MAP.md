# Paper map

## Identity and source boundary

- Paper: *Tuning Transport in Solid-State Bose-Fermi Mixtures by Feshbach
  Resonances*.
- Preprint: arXiv:2409.18176v2.
- Publication: Physical Review Letters **134**, 126502 (2025), DOI
  `10.1103/PhysRevLett.134.126502`.
- Frozen inputs: `raw/paper.pdf` and the manuscript TeX/BibTeX inventory under
  `raw/tex/`.
- The paper points to author data and code on Zenodo. That repository was not
  opened. Author code, numerical arrays, and plotted pixels are forbidden as
  inputs to the numerical implementation.

## Scientific argument

1. A hole and an interlayer exciton resonantly convert into a fermionic trion.
   The detuning moves the trion pole through the hole--exciton continuum.
2. Energy and momentum conservation select a narrow region of the three
   dispersions.  Near equal hole/trion Fermi radii this strongly enhances the
   hole scattering rate.
3. The momentum carried by the selected excitons changes sign across that
   resonance, producing sign-changing exciton drag.
4. The same collision kernel produces a nonmonotonic temperature dependence
   and non-Drude ac conductivities.
5. A three-fluid model gives a closed analytic description of the ac curves
   once its fitted relaxation and drag coefficients are supplied.

## Equation and method inventory

| Card | Source | Numerical role | Boundary |
| --- | --- | --- | --- |
| EQ001 | Main Eq. (1) | three quadratic dispersions and conversion vertex | printed |
| EQ002 | Supplement microscopic-model section | vacuum T matrix and scattering amplitude | sign convention/linewidth not fully fixed |
| EQ003 | main model text plus thermodynamics | chemical equilibrium and density closure | conservation closure derived explicitly |
| EQ004 | Supplement Eqs. (17)--(32) | linearized three-species Boltzmann solver | paper grid and delta regularization omitted |
| EQ005 | Main Eqs. (2)--(3) | on-shell hole rate and resonance detuning | printed |
| EQ006 | Supplement conductivity definition | particle conductivities | printed |
| EQ007 | Supplement Eqs. (39)--(40) | leading-order Kubo check | printed; spectral quadrature reconstructed |
| EQ008 | Supplement Eqs. (41)--(43) | analytic three-fluid ac response | fitted coefficients printed; operating densities reconstructed |
| EQ009 | Main Fig. 3 discussion | acoustic-phonon crossover | cited calibration not printed |

## Numerical evidence map

- T001: the scattering-amplitude series in the right-hand region of Main
  Fig. 1(b).
- T002: all four hole-resistivity curves in Main Fig. 1(c).
- T003: all three exciton-drag curves in Main Fig. 2.
- T004: all three many-body temperature curves in the Main Fig. 3 axes.
- T005: the solid near-resonant **total**-resistivity curve in the Main Fig. 3
  inset.
- T011: the dash-dot far-detuned **total**-resistivity curve in the same inset;
  this item is now generated from the paper's asymptotic Drude-plus-phonon
  limit, with the unpublished absolute phonon calibration kept as a proxy.
- T006--T008: hole, exciton, and trion ac panels of Main Fig. 4; each target
  binds kinetic/fit real and imaginary series separately.
- T009: both density curves in Supplement Fig. 6.
- T010: all three trion-drag curves in Supplement Fig. 7.

The denominator is therefore 30 numerical series, all with runnable
formula-derived implementations.  Eleven non-numerical display items are inventoried and explicitly
excluded.  The full text adds no independent quantitative prose claim beyond
these displayed observables.

The source-only diagrams and sketches are inventoried but not redrawn.  Covered
numeric items are generated from equations.  T011 is independently attested;
its remaining limitation is publication-side phonon calibration, not missing
implementation.
Source figures may be consulted only after numerical arrays are frozen, and
then only by the RenderContract for typography, axes, line styles, colors, and
layout.
