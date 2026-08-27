# Paper Map

## Identity

- Paper ID: `physics-9712001`
- Title: *Real Spectra in Non-Hermitian Hamiltonians Having PT Symmetry*
- Authors: Carl M. Bender and Stefan Boettcher
- arXiv: `physics/9712001v3`
- DOI: `10.1103/PhysRevLett.80.5243`
- Frozen PDF: `raw/paper.pdf`
- Frozen PDF SHA256:
  `6bfed99eb3401c1acaebd3096b8681cc998ab8b318ce4cc54a7c36ec0c66804e`

## Reproduction Goal

Independently solve the PT-symmetric eigenvalue problem

`H = p^2 + m^2 x^2 - (i x)^N`

and reproduce every numerical scientific object in the paper: the massless
spectrum in Fig. 1, both exact/WKB columns in Table I, both exact/asymptotic
columns in Table II, the three printed-mass spectra in Fig. 3, and every
formula/prose claim that admits a numerical falsification test. Fig. 2 is a
conceptual Stokes-wedge diagram and is not rendered as a numerical target, but
its quantitative wedge geometry is tested independently.

## Scientific Structure

| Paper object | Scientific role | Reproduction consequence |
| --- | --- | --- |
| Eq. (1)-(3) | Hamiltonian, complex boundary wedges and contour | defines the non-Hermitian eigenproblem and admissible boundary conditions |
| Fig. 1 | massless real spectrum versus exponent N | independently scan the real eigenvalue branches and locate the first exceptional point as a converged root, without using its printed value as solver input |
| Eq. (4)-(5), Table I | complex WKB quantization | compare independent contour numerics with the closed WKB formula at N=3,4 |
| Eq. (6)-(11), Table II | N=1+epsilon ground-state asymptotics | solve the exact patch condition and the printed implicit asymptotic equation |
| Eq. (12) | classical period | independent numeric target T027 plus subcritical correspondence T028 |
| Fig. 3 | massive spectrum for three printed m^2 values | independently scan all real branches for m^2=3/16,5/16,7/16 |
| Eqs. (4)–(5) prose | complex-WKB applicability | evaluate both turning points, their segment's actual intersection with the principal branch cut, the N=2 transition and contour-deformation invariance |
| Hermitian comparison after Table I | \(|x|^N\) WKB and square-well limit | use a separate real-axis eigensolver through N=512 |
| Table II caption | \((-\ln\epsilon)^{2/3}\) law | fit log-domain roots of Eq. (11) on a declared asymptotic grid |
| Opening examples | PT/non-PT cubics and shifted oscillators | solve or derive every printed low-spectrum claim independently |
| Near-N=2 discussion | exceptional-point merger order | evaluate a complex-symmetric two-level discriminant at two quadrature orders and compare each merger level with turning-point events from an independently integrated classical orbit |
| Massive-case discussion | N=0,1,2 anchors and pairwise transitions | combine exact limits with independent contour spectra |

## Complete Figure and Table Inventory

| Item | Class | Decision |
| --- | --- | --- |
| Main Fig. 1 | numerical spectrum | T001 |
| Main Fig. 2 | formula-derived Stokes-wedge schematic | excluded from numerical reproduction |
| Table I, N=3 | numerical exact/WKB comparison | T002 |
| Table I, N=4 | numerical exact/WKB comparison | T003 |
| Table II | numerical exact/asymptotic comparison | T004 |
| Main Fig. 3, m^2=3/16 | numerical spectrum | T005 |
| Main Fig. 3, m^2=5/16 | numerical spectrum | T006 |
| Main Fig. 3, m^2=7/16 | numerical spectrum | T007 |
| Eq. (5) leading WKB and validity probes | body-level numeric claim | T008 |
| Hermitian \(|x|^N\) comparison | body-level numeric claim | T009 |
| Near-one logarithmic scaling | body-level numeric claim | T010 |
| Opening cubic examples | body-level numeric claims | T011–T012 |
| Four shifted-oscillator spectra | body-level numeric claims | T013–T016 |
| Massless unbroken/broken/N=1 phase claims | body-level numeric claims | T017–T019 |
| Wedge geometry and contour invariance | body-level numeric claims | T020–T021 |
| Turning-point identity and solver cross-check | body-level numeric claims | T022–T023 |
| WKB failure and exact Airy obstruction | body-level numeric claims | T024–T025 |
| Near-N=2 level-merger perturbation | body-level numeric claim | T026 |
| Classical period and spiral correspondence | body-level numeric claims | T027–T028 |
| Massive phase structure | body-level numeric claim | T029 |

There is no supplemental material and no numeric subpanel outside this list.
The authoritative coverage contract contains 27 paper items: four numeric
figure/table families, 22 body-level quantitative claims, and one nonnumeric
schematic. Those items map to 29 atomic targets so a multi-series table or
figure cannot silently stand in for a missing scientific claim.

## Printed and Unprinted Inputs

- The Hamiltonian, boundary wedge centers/openings, WKB formula, both table
  grids and all three Fig. 3 mass values are printed exactly.
- Fig. 1 and Fig. 3 do not print the authors' N sampling grid, finite-domain
  radius, discretization, matrix size or convergence tolerances. The
  reproduction therefore declares and converges these numerical choices; it
  does not infer them from EPS points.
- Table values are comparison anchors only. They are never supplied to an
  eigensolver or used to tune its physical parameters.
