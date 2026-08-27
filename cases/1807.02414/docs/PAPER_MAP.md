# Paper Map

## Identity

- Paper: *Hydrodynamic Diffusion in Integrable Systems*
- Authors: Jacopo De Nardis, Denis Bernard, Benjamin Doyon
- arXiv: 1807.02414
- Publication: *Physical Review Letters* **121**, 160603 (2018)
- DOI: 10.1103/PhysRevLett.121.160603
- Local evidence: `raw/paper.pdf` and `paper-source/hydroviscosity_Final_v4.tex`

## Scientific claim

Elastic two-quasiparticle scattering produces a positive diffusion operator on
top of Euler-scale generalized hydrodynamics. In the XXZ chain this broadens a
weak magnetic domain wall and gives finite spin Onsager coefficients at
root-of-unity anisotropies.

## Structure and evidence

| Paper section | Role in reproduction | Evidence |
| --- | --- | --- |
| Hydrodynamics, Eqs. (1)-(6) | Defines densities, currents, Euler matrix, and dressed velocities | EQ003-EQ004 |
| Diffusion, Eqs. (7)-(12) | Defines the Green-Kubo/Onsager matrix and dressed two-body kernel | EQ005-EQ006 |
| Numerical evaluations, Eq. (13) | Linearized diffusive GHD for a weak wall | EQ007 reduced result; EQ009 full code-ready lane / T001 |
| Main Fig. 1 | Nine numerical series: six GHD curves and three tDMRG marker series | T001 and T003 |
| Numerical paragraph | Three values of `(D C)_SzSz` for ell=3,4,7 | T002 |
| Limiting-case discussion | Hard-rod reduction and free-model zero diffusion | T004 and T005 |
| Entropy paragraph and supplement | Non-negative Navier-Stokes entropy production | T006 |

## Complete numerical inventory

| Atomic item group | Count | Covered | Target and state |
| --- | ---: | ---: | --- |
| Main Fig. 1 Euler GHD series | 3 | 3 | T001, independently generated |
| Main Fig. 1 diffusive GHD series | 3 | 3 | T001, reduced result with evidence cap |
| Main Fig. 1 tDMRG marker series | 3 | 0 | T003, code ready but paper-time execution absent |
| Text spin-Onsager claim | 1 | 1 | T002, independently generated |
| Hard-rod limiting claim | 1 | 0 | T004, target declared; method missing |
| Free-model limiting claim | 1 | 0 | T005, target declared; method missing |
| Entropy-production claim | 1 | 0 | T006, target declared; method missing |
| **Total** | **13** | **7** | **6 items explicitly uncovered** |

The manuscript has no active numerical table and no supplementary numerical
figure. A commented-out table in the TeX repeats the three T002 values and is
not a separate result. The six uncovered items are listed with causes and next
actions in `FIGURE_CLASSIFICATION.md` and `TARGET_LEDGER.md`.
