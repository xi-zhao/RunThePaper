# Paper map

## Identity and source boundary

- Preprint: arXiv:2402.14814v2, 13 January 2025.
- Publication: Physical Review Letters 133, 253401 (2024), DOI
  `10.1103/PhysRevLett.133.253401`.
- Full source: `raw/paper.pdf` (15 pages, including supplement) and two TeX
  files in `raw/tex/`.
- The arXiv inventory has no code or numerical arrays. Author figure PDFs are
  not inputs to the numerical model.

## Scientific argument

1. A two-dimensional oscillator viewed at rotation frequency equal to the trap
   frequency produces degenerate lowest-Landau-level states.
2. For two spinful fermions, the `nu=1/2` Laughlin state is
   `|0>_com |2>_rel`, equivalently a fixed superposition of single-particle
   `m=0,1,2` orbitals.
3. The relative `m=2` node suppresses zero-range interactions while preserving
   strong angular anticorrelation.
4. An anisotropic trap coherently couples relative `m=+2` and `m=-2`, exposing
   the phase winding through Ramsey dynamics.
5. The supplement models the magnetic-field-dependent spectrum using confined
   contact interactions, the Gaussian tweezer's quartic correction, and a
   rotating Laguerre-Gaussian perturbation.

## Numerical evidence map

- Main Fig. 2: rotating oscillator levels and the ideal Rabi observable.
- Main Fig. 3: ideal formula-derived counterparts of the four measured density
  panels; experimental samples remain out of scope.
- Main Fig. 4: all three printed theoretical curves.
- Supplement Fig. S1: all three rotating-frame spectra.
- Supplement Fig. S2: harmonic, quartic, and driven theory panels. The missing
  full coupled-channel map and drive calibration cap these at a reconstructed
  model.
- Supplement Fig. S3: three printed Ramsey fit models and the four-time
  formula-derived density evolution.
- Supplement Fig. S4: the theoretical `1/(2*pi)` line.
- Supplement Fig. S6: both printed Gaussian imaging kernels.

Pure schematics and unpublished experimental samples are not redrawn. Their
scope decisions are explicit in `FIGURE_CLASSIFICATION.md` and
`figure_coverage.json`.
