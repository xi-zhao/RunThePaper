# Paper Map

## Identity

- Paper ID: `2607.22976`
- Title: *Spectral Topology and Non-Bloch Band Theory for Domain-Wall Systems*
- Authors: Mingtao Xu, Rui Wang, Tian-Shu Deng, Wei Yi
- Source: <https://arxiv.org/abs/2607.22976> (v1, 25 July 2026)
- Local PDF: `raw/2607.22976.pdf` (SHA-256 `b7b6f991667ef06c648bb35ffd53909744643388227fa57d8872b5e4752aa224`)
- Local source: `raw/2607.22976-source.tar` (SHA-256 `54f95ccac6ae49a56ead371bbf55ba43599ea67aa988acf4bd59d6e9e06ffd1d`)

## Reproduction Goal

Recompute every numerical main-text and supplemental panel from the Laurent
Hamiltonians, root-modulus GBZ conditions, constrained Ronkin function, and
finite real-space Hamiltonians. Original figure files remain reference-only
and are forbidden inputs to the numerical runner. Schematics are classified
but not redrawn.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Introduction | Defines the domain-wall-ring problem | Separates extended, standing-wave-like, and traveling-wave-like sectors. |
| Topological origin of NHSE | Local winding-mismatch criterion | Right localization at interface `alpha|alpha+1` requires positive relative winding. |
| Ronkin non-Bloch theory | Main constructive method | A constrained convex Ronkin function enforces zero total imaginary gauge. |
| Spectral winding | Boundary sensitivity | Flux winding is carried by traveling-wave branches. |
| SI-SII | Gauge constraint and topology proof | Derives zero-growth condition and Toeplitz-index criterion. |
| SIII-SIV | Boundary determinant and Ronkin derivations | Gives the root ordering and complete Case-I/Case-II GBZ equations used numerically. |
| SV-SVI | Open chain and flux response | Gives Fig. S2 and explains disappearance of the traveling sector after opening the ring. |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| DW001 | Main Eqs. (1)-(5), SI | Laurent bulk model, winding, and finite ring | verified with one disclosed interface convention |
| DW002 | Main Eqs. (8)-(11), SIV | Jensen/root form of constrained Ronkin function | verified |
| DW003 | Main Case I/II, SIII Eqs. (S89)-(S105) | Standing/traveling GBZ classification | verified |
| DW004 | Main Eq. (12), SVI | Flux spectral winding | verified |
| DW005 | SIV Eqs. (S129)-(S134) | Spectral potential and DOS | verified |
| DW006 | SV Eqs. (S135)-(S141) | Open-chain/constituent OBC spectra | verified |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| Fig. 1(a) | General domain-wall-ring sketch | schematic_context | Excluded; explicitly schematic. |
| Fig. 1(b) | Domain-wall-ring schematic eigenspectrum | schematic_context | Excluded; explicitly schematic. |
| Fig. 1(c) | Typical extended-state profile | schematic_context | Excluded; explicitly typical. |
| Fig. 1(d) | Typical standing-wave-like profile | schematic_context | Excluded; explicitly typical. |
| Fig. 1(e) | Typical traveling-wave-like profile | schematic_context | Excluded; explicitly typical. |
| Fig. 2(a) | PBC/DW spectra and winding regions | numeric_reproduction | T001; paper parameters printed. |
| Fig. 2(b) | All right-eigenstate profiles | numeric_reproduction | T001; paper parameters printed. |
| Fig. 2(c) | Representative profiles near interface 2|3 | numeric_reproduction | T001; representative state indices are not reported. |
| Fig. 2(d) | Representative profiles near interface 3|1 | numeric_reproduction | T001; representative state indices are not reported. |
| Fig. 3(a) | Direct-diagonalization and Ronkin spectra | numeric_reproduction | T002. |
| Fig. 3(b) | Constrained Ronkin surface at E1 | numeric_reproduction | T002; exact E1 is not reported. |
| Fig. 3(c) | Constrained Ronkin surface at E2 | numeric_reproduction | T002; exact E2 is not reported. |
| Fig. 3(d) | Constrained Ronkin surface at E3 | numeric_reproduction | T002; exact E3 is not reported. |
| Fig. 3(e) | Domain-wall-ring and individual-domain aGBZ spectra | numeric_reproduction | T002. |
| Fig. 3(f) | Domain-1 GBZ | numeric_reproduction | T002. |
| Fig. 3(g) | Domain-2 GBZ | numeric_reproduction | T002. |
| Fig. 3(h) | Domain-3 GBZ | numeric_reproduction | T002. |
| Fig. 4 | Flux winding and standing/traveling sectors | numeric_reproduction | Targeted. |
| Fig. S1(a) | DOS from the constrained Ronkin minimum | numeric_reproduction | T004; grid resolution is not reported. |
| Fig. S1(b) | DOS from real-space diagonalization | numeric_reproduction | T004; grid resolution is not reported. |
| Fig. S2(a) | Open-chain sketch | schematic_context | Excluded. |
| Fig. S2(b) | Ring and opened-chain spectra | numeric_reproduction | T005. |
| Fig. S2(c) | Constituent-domain OBC spectra | numeric_reproduction | T005. |

## Assumptions And Identified Gaps

- The paper fixes the bulk Laurent coefficients and domain sizes exactly, but
  does not state the finite interface-stencil convention. The implementation
  uses the local row/domain stencil, which has the correct homogeneous Bloch
  limit and changes only finite-interface details.
- The exact eigenstate indices used in Fig. 2(c,d) and the exact reference
  energies `E1-E3` used in Fig. 3(b-d) are absent from the text and source.
  They are selected by deterministic physics criteria, never by digitizing the
  source figure, and therefore those panels are labelled `paper_subset`.
- The TeX archive contains no author numerical code or data.
