# Paper Map

## Identity

- Paper ID: `2404.08378`
- Title: *On-Chip Quantum Interference between Independent Lithium Niobate-on-Insulator Photon-Pair Sources*
- Authors: Robert J. Chapman et al.
- Source: Phys. Rev. Lett. 134, 223602 (2025), DOI `10.1103/n2y3-2bmz`
- Local PDF: `paper-source/prl-134-223602.pdf`
- Local supplement: `paper-source/LNOI_Quantum_Interference_SM.pdf`
- Local manuscript source: `paper-source/2404.08378-source.tar`

## Reproduction Goal

Independently derive the two-photon Mach-Zehnder transformation and reproduce
every formula-defined numerical panel or subpanel.  Experimental point arrays
are not public, so those components are fail-closed rather than digitized from
the published images.  Device schematics, microscope images, and fabrication
photographs are contextual, not numerical reproduction targets.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Main text, Eqs. (1)–(4) | Scientific core | N00N input state, MZI unitary, and ideal output state. |
| Main Figs. 1–4 | Device, transfer curves, two-photon interference, HOM test | Numeric theory is targeted; unreleased measurements remain deferred. |
| Supplement Sec. I | Imperfection model | Imbalance and partial indistinguishability scans in Figs. S1–S2. |
| Supplement Secs. II–III | Fabrication and setup | S3 is microscopy; S4 is unreleased coincidence data. |
| Supplement Sec. IV | Bandwidth and loss | HOM visibility integral, spectral filtering, coupler loss, and electrode-loss simulation. |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQC001 | Main Eqs. (1)–(2) | Balanced and imbalanced N00N input state | frozen |
| EQC002 | Main Eq. (3) | Single-photon MZI unitary | frozen |
| EQC003 | Main Eq. (4) | Two-photon output probabilities | frozen |
| EQC004 | Supplement Eqs. (1)–(2) | Source imbalance and coherence/purity | frozen |
| EQC005 | Main Fig. 2 and Eq. (3) | Classical MZI transfer probabilities | frozen |
| EQC006 | Supplement Eqs. (3)–(4) | Reflectivity-dependent HOM visibility | frozen |
| EQC007 | Main Fig. 4 text | Gaussian HOM delay model and bandwidth conventions | frozen |
| EQC008 | Main brightness paragraph | Coincidence-loss-pump arithmetic | frozen |
| EQC009 | Main Fig. 1(c) and Supplement Fig. S7 | Scalar Helmholtz mode and evanescent metal-overlap reconstruction | reconstruction |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| Fig. 1(a,b) | Chip and cross-section schematics | nonnumeric | Excluded. |
| Fig. 1(c) | 781/1562 nm optical modes | numeric simulation | T001. |
| Fig. 1(d) | SHG spectra for two sources | numeric experiment | Missing author arrays. |
| Fig. 2 | Four classical MZI transfer curves | mixed numeric | T002 model; points deferred. |
| Fig. 3(a) | Experimental setup | nonnumeric | Excluded. |
| Fig. 3(b–g) | Three two-phase surfaces and three phase cuts | mixed numeric | T003–T008 theory; rate arrays deferred. |
| Fig. 4(a,b) | HOM setup and delay scan | mixed | T009 theory; coincidence points deferred. |
| Fig. S1 | Imbalance scans | numeric simulation | T010–T011. |
| Fig. S2 | Purity scans | numeric simulation | T012–T013. |
| Fig. S3 | Two-photon microscopy | nonnumeric | Excluded. |
| Fig. S4 | CAR delay histograms | numeric experiment | Missing author arrays. |
| Fig. S5(a–d) | Reflectivity, HOM visibility, spectrum, grating efficiency | mixed numeric | T014 formula; source curves deferred. |
| Fig. S6 | Directional-coupler loss | mixed numeric | T015 theory; points deferred. |
| Fig. S7 | Electrode loss versus gap | numeric simulation | T016. |
| Printed quantitative claims | Brightness and bandwidth normalizations | numeric | T017–T018. |

## Assumptions

- Published scalar parameters and equations may configure the independent model.
- Author figure pixels may be viewed only after numerical arrays are frozen and
  never enter the runner, fitting, or scientific score.
- The public source archive contains manuscript TeX and figure PDFs only; it
  contains no evaluation code or point-level numerical arrays.
- Scalar mode and metal-loss calculations are declared reconstructions because
  the full fabrication mesh, dispersive material database, and solver settings
  are not published.
