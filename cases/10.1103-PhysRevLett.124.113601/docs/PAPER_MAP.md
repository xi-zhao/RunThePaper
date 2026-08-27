# Paper Map

## Identity

- Paper ID: `10.1103-PhysRevLett.124.113601`
- Title: *Localization Driven Superradiant Instability*
- Authors: Honghao Yin, Jie Hu, An-Chun Ji, Gediminas Juzeliunas, Xiong-Jun Liu, Qing Sun
- Formal publication: *Physical Review Letters* **124**, 113601 (2020)
- DOI: `10.1103/PhysRevLett.124.113601`
- Preprint: arXiv:`1909.08125`
- Local PDF: `raw/paper.pdf`
- Local supplement: `raw/supplementary.pdf`
- Local source: `paper-source/disorder-superradiance.tex`

## Reproduction Goal

Independently reproduce every numerical figure in the published paper and
supplement that is closed by the published single-particle/mean-field model:

- Fig. 2: GAA mobility edge, IPR, and state-resolved critical pump;
- Fig. 3: AA susceptibility, critical threshold, momentum distributions, and
  state-resolved susceptibility channels;
- Fig. 4: self-consistent photon number and the critical-pump landscape;
- Fig. S1: self-consistent atomic density profiles.

Fig. 1 is apparatus context and is not a numerical target. The paper's final
sentence about many-body localization is prospective, not a solved many-body
target. No source panel or digitized curve may be used as generated physics
data.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Model construction, pp. 1-2 | Defines AA/GAA lattice and cavity coupling | Eqs. (1)-(3) |
| Mobility-edge result, pp. 2-3 | Central state-resolved instability claim | Fig. 2 |
| Linear-response derivation, pp. 3-4 | Connects overlaps to susceptibility and threshold | Eqs. (4)-(7), Fig. 3 |
| Mean-field observable, p. 4 | Photon-number and wave-vector predictions | Fig. 4 |
| Supplement Sec. I | Derives cavity-mediated global interaction | Eqs. (S1)-(S6); contextual for this mean-field case |
| Supplement Sec. II | Self-consistent density evidence | Fig. S1 |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | Main Eq. (1) | AA Hamiltonian | source traced |
| EQ002 | Main Eq. (2) | GAA corrections | source traced |
| EQ003 | Main Eq. (3) | Steady-state cavity amplitude | source traced |
| EQ004 | Main Eqs. (4)-(6) | Eigenbasis equations and scattering overlaps | source traced |
| EQ005 | Main Eq. (7) | Critical pumping threshold | derivation required |
| EQ006 | Fig. 2 text | IPR and localized-state self-scattering rule | derivation required |
| EQ007 | Fig. 3 text | Momentum distribution and channel susceptibility | source traced |
| EQ008 | Supplement Sec. II | Self-consistent effective Hamiltonian | reconstructed from Eqs. (S1)-(S5) |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| Fig. 1 | BEC-cavity-lattice apparatus | schematic context | no numerical reproduction |
| Fig. 2 | State-resolved `eta_c` and GAA IPR | numeric reproduction | central mobility-edge target |
| Fig. 3 | Threshold, susceptibility, momentum, and channels | numeric reproduction | central AA mechanism target |
| Fig. 4(a) | Steady-state photon number vs pump | numeric reproduction | added in published version; absent from arXiv source figure |
| Fig. 4(b) | Threshold vs cavity wave-vector | numeric reproduction | source Fig. 4 is available |
| Fig. S1 | Self-consistent density distributions | numeric reproduction | pump values are not printed |

## Assumptions

- Fig. 2 uses periodic boundaries: they remove four finite-chain edge-state IPR
  spikes that are absent from the source figure while preserving the printed
  mobility-edge energy. Fig. S1 uses open boundaries, inferred from its
  `chi=0` sine-envelope density. Boundary choice is target-local, not global.
- Site indices are zero-based in code. Fig. 2 applies the source-vector-fixed
  one-site phase shift; Fig. S1 applies a separately reconstructed finite-chain
  origin because its pump samples and phase convention are not printed.
- Energies and couplings are measured in units of `J`.
- The exact golden ratio is used for every numerical target. For Fig. 2, the
  PDF vector path fixes this convention unambiguously: it reproduces all 377
  IPR samples with `r=0.99999999997`, whereas the caption's `233/377` is the
  finite rational description. Fig. S1 keeps its phase/origin explicitly
  reconstructed because the supplement does not fully fix them.
- `U/J=0.1` is inherited from Fig. 2 for Figs. 3-4. The literal published
  Eq. (7) then gives `eta_c/J=0.206406` at `chi=0`; the plotted `0.2768`
  normalization is preserved as a fresh-review discrepancy, not used to tune
  the runner.
- Published equations/captions supersede arXiv v1 when they differ. The arXiv
  source remains a provenance and original-figure reference.
