# Paper Map

## Identity

- Paper ID: 2607.02157
- Title: Thermodynamics of Quantum Reservoir Computing
- Authors: Lixiang Ding, Xingze Qiu (Tongji University)
- Source: arXiv:2607.02157v1 [quant-ph], 2 Jul 2026 (user-provided PDF)
- Local PDF: `raw/paper.pdf` (31 pages: 13 main text + Methods, 18 Supplementary Information)
- Local source: no TeX source ingested (PDF only; arXiv source not downloaded)
- Publication status: `unpublished` preprint (v1); no formal publication verified

## Reproduction Goal

Reproduce the numerical content of the paper's thermodynamic framework for
quantum reservoir computing (QRC):

1. the driven open many-body simulation (collisional thermalization map) for
   the two reservoir architectures (disordered TFIM and augmented cluster model);
2. the Holevo memory/predictive capacities, quantum informational dissipation
   (QID), coherence decomposition, and generalized Landauer bound curves of
   Fig. 2 (six panels + two insets);
3. the spectral-resonance analytics of Fig. S1 (accumulation factor G(omega),
   MG signal spectrum, many-body energy spectra vs J and alpha);
4. the multi-step capacities and NMSE of Fig. S2.

Out of scope: Fig. 1 (framework schematic, no numerical content).

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Main: QRC formalism (Eqs. 1-3) | model + task definition | master equation, CPTP map, ridge readout, NMSE |
| Main: Information capacities (Eqs. 4-10) | core observables | conditional ensembles, Holevo chi^m / chi^p, QID chi^d |
| Main: Coherence decomposition (Eqs. 11-12) | observable split | chi = I + C; QID = D^c + D^q |
| Main: Generalized Landauer bound (Eqs. 13-16) | thermodynamic bound | per-step identity beta*W_irr = chi^d; cumulative bounds |
| Main: Quantum critical thermodynamics (Eq. 17, Fig. 2) | main numerical results | both architectures, L=6, capacity/Landauer/coherence peaks |
| Methods (Eqs. 18-21) | numerical protocol | MG generation, collisional map, binning estimator B=50 |
| SI I-II | thermodynamic consistency | global Davies-Lindblad derivation; ensemble marginalization |
| SI III (S10-S52, Fig. S1) | analytics | BKM metric, analytic chi^m/chi^p (S41/S42), G-factor resonance (S43-S52) |
| SI IV (S53-S61) | coherence bounds | chi = I + C proof; Markovian D^q >= 0 proof |
| SI V (S62-S73) | Landauer derivation | work/heat bookkeeping, W_relax >= 0, Landauer decomposition |
| SI VI (S74-S80, Fig. S2) | multi-step extension | tau-delayed memory, h-step prediction, NMSE validation |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQC001 | Eq. 19 / S7 | collisional CPTP map (simulation engine) | see EQUATION_CARDS.json |
| EQC002 | Eq. 18 + Methods | Mackey-Glass drive generation + preprocessing | see EQUATION_CARDS.json |
| EQC003 | Eq. 8 / S13 | Holevo memory capacity | see EQUATION_CARDS.json |
| EQC004 | Eq. 9 / S21 | Holevo predictive capacity | see EQUATION_CARDS.json |
| EQC005 | Eq. 10 | quantum informational dissipation (QID) | see EQUATION_CARDS.json |
| EQC006 | Eq. 11 / S55 | coherence decomposition chi = I + C | see EQUATION_CARDS.json |
| EQC007 | Eq. 12 / S56 | QID split D^c + D^q | see EQUATION_CARDS.json |
| EQC008 | S62 | injection work from conditional ensembles | see EQUATION_CARDS.json |
| EQC009 | Eq. 13 / S64 | per-step identity beta*W_irr = chi^d | see EQUATION_CARDS.json |
| EQC010 | Eqs. 14-15 / S68-S71 | generalized Landauer bound, W_relax >= 0 | see EQUATION_CARDS.json |
| EQC011 | Eq. 17 / S41-S42 | BKM analytic capacities (linear response) | see EQUATION_CARDS.json |
| EQC012 | S43, S49, S52 | accumulation factor G and resonance peak | see EQUATION_CARDS.json |
| EQC013 | Main text p.7 | reservoir Hamiltonians (disordered TFIM, cluster) | see EQUATION_CARDS.json |
| EQC014 | Eqs. 2-3 | ridge readout and NMSE | see EQUATION_CARDS.json |
| EQC015 | S57-S61 | Markovian bound D^q >= 0 | see EQUATION_CARDS.json |
| Binning estimator | Eqs. 20-21 + Methods | conditional-state estimation protocol | protocol, implemented in code |

## Figure/Table Inventory

The W1 whole-paper audit atomizes every independently judgeable plotted series,
inset series, and jointly adjudicated spectrum family.  It finds **46 display
items: 43 eligible numerical items and 3 excluded schematics**.  Supporting
derivations remain formula evidence for these displays and are not counted a
second time as standalone claims.

| Item | Atomic inventory | Class | W1 scope result |
| --- | ---: | --- | --- |
| Fig. 1(a-c) | 3 panels | schematic_context | 3 excluded: no plotted numerical observable |
| Fig. 2(a1-c2) | 18 series | numeric_reproduction | 18/18 mapped to T001 and backed by the frozen TFIM/cluster scans |
| Fig. S1(a-c) | 7 series/families | numeric_reproduction | 7/7 mapped to T002, including the signal/statistics insets |
| Fig. S2(a1-c2) | 18 series | numeric_reproduction | 18/18 mapped to T003 across both models and all delays/horizons |

Machine-readable item identities and paper locations live in
`figure_coverage.json`.  At this audit layer there is no uncovered eligible
item; later evidence gates remain separate from scope coverage.

## Key Numerical Protocol (Methods)

- MG drive: dx/dt = 0.2 x(t-18)/(1+x^10(t-18)) - 0.1 x(t); RK4; discard transient;
  sample at interval 3; linearly rescale to [-1,1]. Approx. zero mean, stationary
  variance sigma_s^2 ~= 0.11; dominant spectral peak omega_s ~= 0.36.
- Reservoir: L=6 spins; H_{t_n} = H0 + s_n * lambda * H1; H1 = sum_i sigma^z_i; lambda = 0.05.
- Map: rho_{n+1} = (1-P_th) U rho U^dag + P_th rho^eq(s_n); U = exp(-i H_{t_n} dt);
  P_th = 1 - exp(-gamma0 dt); gamma0 = 0.1, dt = 1, beta = 1 (P_th ~= 0.0952).
- Estimation: ensemble of 5000 independent MG sequences; at each step bin the density
  matrices by the scalar value of s_n (memory) or s_{n+1} (predictive) into B=50
  uniform bins over [-1,1]; P_b = relative frequency; rho_b = bin average;
  entropies with eigenvalue truncation 1e-12.
- Fig. 2 protocol: N_wash=500 then N_eval=2000 accumulation steps; averages over 5000
  sequences; disordered TFIM additionally averaged over 100 random realizations
  (5000 sequences each). NMSE: N_wash=500, N_train=2000, N_test=2000, eta=1e-5,
  500 sequences, full Pauli observable basis.
- Coherence basis B = computational (sigma^z product) basis, in which H1 is diagonal.

## Assumptions

- The dephasing basis B for C(rho) is the sigma^z product (computational) basis;
  stated indirectly ("driving operator H1 strictly diagonal in the dephasing basis").
- Cluster-chain boundary condition is unpublished; resolved to OPEN by the PBC
  duality-symmetry contradiction and the Fig. S1c spectral fingerprint (see
  DERIVATION_TRACE.md, EQC013).
- "Full Pauli basis" readout = all 4^L - 1 nontrivial Pauli-string expectation values.
- The disordered-TFIM J axis in Fig. 2 (1e-1..1e2) is sampled logarithmically; exact
  grid not published. Cluster-model alpha axis 0..1, exact grid not published.
- Fig. S1b normalization: "energy levels for each J are normalized by the total
  spectral width" (stated in caption).
- MG initial conditions / seed values are not published; only the ensemble statistics
  are reproducible, not per-sequence traces.
