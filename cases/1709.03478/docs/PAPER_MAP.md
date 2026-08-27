# Paper Map

## Identity

- Paper ID: arXiv:1709.03478 (v1, 12 September 2017)
- Preprint title: *Exploring the Single-Particle Mobility Edge in a
  One-Dimensional Quasiperiodic Optical Lattice*
- Published title: *Single-Particle Mobility Edge in a One-Dimensional
  Quasiperiodic Optical Lattice*
- Authors: Henrik P. Lüschen, Sebastian Scherg, Thomas Kohlert, Michael
  Schreiber, Pranjal Bordia, Xiao Li, S. Das Sarma, and Immanuel Bloch
- Formal publication: *Physical Review Letters* **120**, 160404 (2018),
  DOI `10.1103/PhysRevLett.120.160404`
- Local PDF: `raw/1709.03478.pdf`
- Local TeX/source: `paper-source/SPME.tex`
- Method context: Li, Li, and Das Sarma, *Phys. Rev. B* **96**, 085119
  (2017), arXiv:1704.04498; paper/source stored reference-only under
  `references/literature/`.

## Reproduction Goal

Independently solve the paper's continuum bichromatic single-particle
Hamiltonian, prepare the stated charge-density-wave and central-cloud initial
states, and test the two-observable signature of the intermediate phase:
simultaneously nonzero imbalance and edge density. Reproduce every theoretical
numerical panel at a declared scale. Experimental points and error bars remain
in the full-paper inventory as comparison evidence, but are excluded from the
theory denominator because they require new measurements and unpublished
shot-level data. The incomplete tube population distribution remains a
parameter/evidence limit on the adjacent theoretical tube-average targets.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Introduction / Fig. 1 | Product claim | Explains why \(\mathcal I>0\) and \(\mathcal E>0\) imply coexistence. |
| Experiment | Physical model | Defines the continuum bichromatic Hamiltonian, wavelengths, and observables. |
| Expansion vs. edge density / Fig. 2 | Dynamic validation | Compares experimental cloud expansion to independently calculable edge density. |
| Results / Figs. 3–4 | Main numerical claim | Locates extended, intermediate, and localized regimes for \(V_p=4,6,8\). |
| Supplement S1 | Observable robustness | Compares FWHM, edge density, and RMS cloud size, with/without a weak trap. |
| Supplement S2 | Finite-time support | Compares 200-tau experiment to 3000-tau theory at \(V_p=4\). |
| Supplement fit functions | Experimental analysis | Defines empirical fits; no raw experimental measurements are supplied. |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQC001 | main Eq. (1) | Continuum bichromatic Hamiltonian | source-traced |
| EQC002 | independent derivation | Dimensionless finite-difference operator | verified |
| EQC003 | Fig. 2 caption + primary band | Convert paper time \(t/\tau\) to Hamiltonian phase | verified |
| EQC004 | main text | CDW imbalance | verified |
| EQC005 | main text | Center-third edge density | verified |
| EQC006 | spectral theorem | Noninteracting one-body evolution | verified |
| EQC007 | supplement S1 | FWHM and RMS expansion observables | reconstructed |
| EQC008 | supplement tube-averaging section | Beam-profile tube average | reconstructed, metadata-limited |
| EQC009 | Fig. 3 caption | 0.015 numerical boundary rule | source-traced |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Decision |
| --- | --- | --- | --- |
| Main Fig. 1 | Experimental/phase schematic | non-numeric schematic | exclude |
| Main Fig. 2(a) | Experimental FWHM traces | numeric experiment | exclude; comparison for T002 |
| Main Fig. 2(b) | Theoretical edge-density traces | numeric theory | reproduce |
| Main Fig. 3(a) | Experimental imbalance/expansion sweep at \(V_p=4\) | numeric experiment | exclude; comparison for T003 |
| Main Fig. 3(b) | Experimental imbalance/expansion sweep at \(V_p=6\) | numeric experiment | exclude; comparison for T003 |
| Main Fig. 3(c) | Experimental imbalance/expansion sweep at \(V_p=8\) | numeric experiment | exclude; comparison for T003 |
| Main Fig. 3(d) | Theoretical imbalance/edge-density sweep at \(V_p=4\) | numeric theory | reproduce |
| Main Fig. 3(e) | Theoretical imbalance/edge-density sweep at \(V_p=6\) | numeric theory | reproduce |
| Main Fig. 3(f) | Theoretical imbalance/edge-density sweep at \(V_p=8\) | numeric theory | reproduce |
| Main Fig. 4, main theory series | Tube-averaged theoretical phase boundaries | numeric theory series | reproduce |
| Main Fig. 4, inset theory | Central-tube theoretical phase boundaries | numeric theory panel | reproduce |
| Main Fig. 4, experimental points | Experimentally fitted phase boundaries | numeric experiment series | exclude; comparison for T004 |
| Supp. Fig. S1(a) | FWHM traces without trap | numeric theory | reproduce |
| Supp. Fig. S1(b) | Edge-density traces without trap | numeric theory | reproduce |
| Supp. Fig. S1(c) | RMS traces without trap | numeric theory | reproduce |
| Supp. Fig. S1(d) | FWHM traces with weak trap | numeric theory | reproduce |
| Supp. Fig. S1(e) | Edge-density traces with weak trap | numeric theory | reproduce |
| Supp. Fig. S1(f) | RMS traces with weak trap | numeric theory | reproduce |
| Supp. Fig. S2, theory series | Theoretical 3000-tau imbalance and edge-density sweep | numeric theory series | reproduce |
| Supp. Fig. S2, experiment series | Experimental 200-tau imbalance and fit | numeric experiment series | exclude; comparison for T006 |

There are 20 atomic displayed items: 13 theoretical numerical items and 7
experimental/schematic exclusions. There are no numerical tables in the target
paper or supplement, and no standalone quantitative claim needs a separate
denominator because the relevant claims are already represented by these
displayed items.

## Assumptions and disclosed gaps

- The continuum coordinate is \(s=x/a\), with \(a=\lambda_p/2\), so the
  kinetic coefficient is \(-1/\pi^2\) in recoil-energy units.
- Open boundaries are used, matching cloud-release dynamics. The source does
  not state boundary conditions for every target-paper calculation.
- The target paper gives \(L=369\) only for Supplementary Fig. S1; the linked
  theory paper reports \(L=738\) for phase sweeps. Local sweeps therefore use a
  declared smaller \(L\), while preserving the paper's potential depths,
  wavelength ratio, times, and observables.
- Main theoretical sweeps use the stationary diagonal ensemble, matching the
  smooth theory curves in Fig. 3. Supplementary Fig. S2 is separately
  propagated to the explicitly stated \(3000\tau\); \(200\tau\) applies to its
  experimental imbalance points.
- Relative lattice phase is averaged over deterministic phases, but six-phase
  experimental shot data are not available.
- Tube averaging is a documented proxy derived from quoted beam/cloud widths;
  the exact per-tube atom histogram is missing, so it cannot be `paper_exact`.
