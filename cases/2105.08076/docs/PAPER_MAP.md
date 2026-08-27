# Paper Map

## Identity

- Paper ID: `2105.08076`
- Title: *Measurement-Induced Dark State Phase Transitions in Long-Ranged Fermion Systems*
- Authors: T. Mueller, S. Diehl, M. Buchhold
- Publication: *Physical Review Letters* **128**, 010605 (2022)
- DOI: `10.1103/PhysRevLett.128.010605`
- Source: arXiv:2105.08076, version dated 25 May 2021
- Local PDF: `raw/paper.pdf`
- Local source: `raw/arxiv-source.tar`

## Reproduction Goal

Independently implement the monitored free-fermion stochastic evolution and the
replica dark-state scaling theory, then reproduce every numerical panel in the
main text and supplement.  Scientific inputs come only from the printed model,
equations, captions, and independently selected convergence settings.  Author
code, author arrays, curve digitization, and source-image pixels are excluded
from the scientific runner.

Fig. 1(a,b) are schematics and therefore excluded.  All remaining plotted
panels are numerical targets.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Microscopic model | Defines long-range hopping and the number-monitoring SSE | Half-filled ring, Neel initial state, `p>1` |
| Observables | Defines trajectory-averaged entropy and density correlations | Evaluated from Gaussian one-body projectors |
| Phase structure | Gives the numerical classifiers and scaling fits | CFT, area-law, and algebraic phases |
| RG analysis | Establishes the threshold `p_c=3/2` | Provides an independent analytic lane |
| Algebraic phase | Gives `b=3/2-p`, `a=p+1/2`, and `b=2-a` | Central scientific claim |
| Supplement: numerical procedure | Defines CFT collapse and finite-size ansatz | No time step, trajectory count, or stationary-time tolerance is printed |
| Supplement: dark state | Derives the long-wavelength covariance | Used for independent exponent and kernel checks |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | Main Eq. (2) | Long-range single-particle Hamiltonian | verified |
| EQ002 | Main Eq. (1) | Continuous number-monitoring trajectory equation | verified |
| EQ003 | Main Eqs. (4a,b) | Gaussian entropy and correlation observables | reconstructed and checked |
| EQ004 | Main Eq. (4b) | Wick sign audit for connected density covariance | source discrepancy open |
| EQ005 | Supplement Eqs. (7)-(9) | Finite-size scaling and fit contracts | verified |
| EQ006 | Main Eq. (3c), supplement Eqs. (1)-(5) | Replica long-range term and doubled exponent | verified |
| EQ007 | Supplement Eqs. (10)-(13) | Infrared kernel and `p_c=3/2` | verified |
| EQ008 | Main Eqs. (8)-(10), supplement Eqs. (14)-(19) | Dark-state covariance and exponents | verified |
| EQ009 | Main Eqs. (6)-(7), supplement Eqs. (20)-(23) | First-order RG flow | verified |

## Figure Inventory

| Item | Caption summary | Class | Target |
| --- | --- | --- | --- |
| Main Fig. 1(a) | Long-range hopping and monitoring cartoon | schematic | excluded |
| Main Fig. 1(b) | Qualitative phase diagram | schematic | excluded |
| Main Fig. 1(c) | Effective-central-charge phase map at `L=600` | numerical | T001 |
| Main Fig. 1(d) | Fitted correlation exponent `a` | numerical | T002 |
| Main Fig. 1(e) | Fitted entropy exponent `b` | numerical | T003 |
| Main Fig. 2(a) | Half-chain entropy versus system size | numerical | T004 |
| Main Fig. 2(b) | Opposite-point correlation versus system size | numerical | T005 |
| Main Fig. 3(a) | Effective central charge versus `1/p` and `L` | numerical | T006 |
| Main Fig. 3(b) | Algebraic-phase `S(l)` and `20 l^2 C(l)` | numerical | T007 |
| Supplement Fig. 1(a) | Subsystem entropy scaling and central-charge inset | numerical | T008 |
| Supplement Fig. 1(b) | Subsystem correlation scaling and exponent inset | numerical | T009 |

## Frozen Scientific Assumptions

- Ring separation is the minimum periodic lattice distance.  The paper writes
  `|s-m|` on a ring but does not spell out its finite-size convention.
- The QSD is integrated by a symmetric unitary/measurement split step.  The
  measurement exponential is derived from the printed normalized Ito equation;
  QR re-orthonormalization keeps each trajectory a pure Slater determinant.
- Time step, stationary time, burn-in, trajectory count, and fitting weights are
  absent from the paper.  They are independently converged and never promoted
  to paper-exact parameters.
- The plotted positive `C` is implemented as `|G_xy|^2`.  The literal connected
  density covariance is also computed and has the opposite sign by Wick's
  theorem; this is retained as a paper-audit discrepancy.
- Captions assign `(gamma=0.3,p=1.25)` to the CFT phase and
  `(gamma=0.3,p=5)` to the algebraic phase, while the equations, plot slopes,
  colors, and surrounding prose imply the reverse.  Both the printed labels and
  the physics-consistent mapping are recorded; scientific code uses the printed
  parameter pairs, never pixels.
