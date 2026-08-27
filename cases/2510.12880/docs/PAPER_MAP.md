# Paper Map

## Identity

- Paper ID: `2510.12880`
- Preprint title: *The Kitaev-AKLT model*
- Published title: *Exact Fractionalized Ground States in an Extended Spin-1
  Kitaev Chain*
- Authors: Alwyn Jose Raja and R. Ganesh
- Source: arXiv:2510.12880; Phys. Rev. Lett. 137, 046701 (2026)
- Local PDF: `raw/paper.pdf`
- Local source: `paper-source/KitaevAKLT.tex`

## Reproduction Goal

Reconstruct the derivation before numerical work, independently reproduce the
two overlap panels of Main Fig. 5, and audit every independent quantitative or
analytic result in the main text and supplement. The existing calculation:

1. use the exact bond conserved quantities to block-diagonalize the spin-1
   Hamiltonian;
2. construct the published bond-dimension-four fractionalized MPS from the
   \(B\), \(M\), and \(A\) tensors;
3. compare the uniform-\(w=+1\) MPS with the exact ground state;
4. compare a one-\(w\)-flip MPS with the corresponding exact first-excited
   sector;
5. verify the projector identity, exact-point zero modes, and product-state
   energy bounds as independent controls.

The full-paper inventory also exposes five supplemental claim families that
the existing periodic-chain implementation does not cover: three open-chain
results, one fractionalized-state parity rule, and one perturbative-sector
claim. They are V003-V007 and remain explicit uncovered items.

The paper supplies plotted overlap points but not their numerical table.
Scientific coverage therefore comes from independent exact diagonalization;
the source PNGs are used only as visual/digitized references.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Model | Defines the alternating X/Y bilinear-biquadratic chain | \(K=\cos\theta\), \(Q=\sin\theta\), even \(N\), periodic boundary |
| Exactly solvable point | Rewrites \(K=Q>0\) as positive projectors | Core frustration-free argument |
| Fractionalized construction | Builds \(2^N\) projected spinon wavefunctions | Singlet/triplet choice on each bond |
| Additional ground state | Adds the antisymmetric product-state combination | Gives total degeneracy \(2^N+1\) |
| MPS and conserved quantities | Orthogonalizes states by \(w_j=\pm1\) | Produces a bond-dimension-four physical MPS |
| Phase diagram | Identifies doubly-degenerate and unique-ground-state regimes | Main Fig. 4 is a schematic summary |
| Spin-1 Kitaev model | Tests ground and first-excited MPS ansätze | Main Fig. 5 is the numerical reproduction target |
| Supplement | Gives spin matrices, projectors, edge counting, MPS tensors, and bounds | Supplies the executable algebra |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQC001 | Supplement, “Convention for spin-1 matrices” | Spin-1 and Cartesian-basis conventions | verified |
| EQC002 | Main Eqs. `eq.H`, `eq.Ws` | Hamiltonian and commuting bond sectors | verified with one source typo recorded |
| EQC003 | Main `eq.Hproject`; supplement projector section | Projector identity at \(\theta=\pi/4\) | verified |
| EQC004 | Main fractionalized construction | Why every bond-state MPS is frustration free | verified |
| EQC005 | Main `eq.Waction`, `eq.Hwpert` | Cluster-stabilizer action in bond variables | verified |
| EQC006 | Main `eq.A_matrices` | Exact cluster-state MPS | verified |
| EQC007 | Supplement, bond-dimension-four matrices | Physical spin-1 MPS tensor | verified algebraically |
| EQC008 | Main Fig. 5 discussion | Ground-state fidelity | verified definition |
| EQC009 | Main Fig. 5 discussion | First-excited-subspace fidelity | verified definition |
| EQC010 | Main/supplement product-state arguments | Exact energy bounds and phase controls | verified |
| EQC011 | Main exact-point claims and uniform \(w=-1\) supplement | \(2^N+1\) degeneracy decomposition | verified |
| EQC012 | Supplement, “Edge states” | open exact-point degeneracy \(2^{N+1}-1\) | source-only; V003 uncovered |
| EQC013 | Supplement, purely biquadratic \(\theta=\pi/2\) | open-chain degeneracy \(2N+1\) | source-only; V004 uncovered |
| EQC014 | Supplement, purely biquadratic \(\theta=3\pi/2\) | open energy \(-(N-1)\) and fourfold degeneracy | source-only; V005 uncovered |
| EQC015 | Supplement, fractionalized variational ansatz | even triplet-parity selection | source-only; V006 uncovered |
| EQC016 | Supplement, bond-conserved perturbation section | second-order onset and all-order uniform-positive-\(w\) sector | source-only; V007 uncovered |

## Figure Inventory

| Item | Caption summary | Initial class | Decision |
| --- | --- | --- | --- |
| Main Fig. 1 | Fractionalized spinon cartoon | schematic_context | excluded |
| Main Fig. 2(a) | Alternating direct-product states | schematic_context | excluded; periodic energy claim belongs to V002 |
| Main Fig. 2(b) | Uniform-z direct-product state | schematic_context | excluded; periodic energy claim belongs to V002 |
| Main Fig. 3(a) | Fractionalized-state MPS | algorithm_trace | excluded; algebra belongs to V001 |
| Main Fig. 3(b) | Cluster-state MPS | algorithm_trace | excluded |
| Main Fig. 3(c) | Physical bond-dimension-four MPS | algorithm_trace | excluded; algebra belongs to V001 |
| Main Fig. 4 | Circular phase diagram | schematic_context | excluded; claims checked by V002 |
| Main Fig. 5(a) | Ground-state/MPS overlap versus \(N\) | numeric_reproduction | T001 |
| Main Fig. 5(b) | First-excited-subspace/MPS overlap versus \(N\) | numeric_reproduction | T002 |
| Supplemental Fig. 1 | Open-chain edge spinons | schematic_context | excluded as image; surrounding \(2^{N+1}-1\) claim is V003 and uncovered |
| Supplemental Fig. 2 | Four-dimensional MPS contraction | algorithm_trace | excluded; algebra checked by V001 |
| Supplemental Fig. 3 | \(C\)-to-\(D\) contraction | algorithm_trace | excluded |
| Supplemental Fig. 4 | Nonzero \(D\)-matrix products | algorithm_trace | excluded |

## Independent Claim Inventory

| Target | Scientific object | Coverage |
| --- | --- | --- |
| V001 | periodic exact-point projector, MPS, and \(2^N+1\) manifold | covered |
| V002 | periodic phase/product-state controls | covered |
| V003 | open exact-point degeneracy \(2^{N+1}-1\) | uncovered |
| V004 | open \(\theta=\pi/2\) degeneracy \(2N+1\) | uncovered |
| V005 | open \(\theta=3\pi/2\) energy and fourfold degeneracy | uncovered |
| V006 | \(\theta=0\) even triplet-parity selection | uncovered |
| V007 | perturbative uniform-positive-\(w\) mechanism | uncovered |

Main Fig. 5(a-b) supply T001-T002. Their surrounding prose is retained as
supporting evidence and is not counted a second time.

## Assumptions And Source Issues

- Site and bond indices are implemented from zero. Bond \(j\) joins sites
  \(j\) and \(j+1\bmod N\); even bonds are X bonds and odd bonds are Y bonds.
- The second exponential in the printed definition of
  \(\hat W_{2j+1}\) is missing a factor of \(\pi\). The surrounding text,
  the assertion \(W_j^2=1\), and the entire supplement require
  \(e^{i\pi S^x}\) on both sites.
- The supplement twice prints \(M^{+1}B^\chi\) where the zero-spin component
  must be \(M^0B^\chi\). The executable tensor is derived from the earlier
  definitions of \(M^s\), \(B^\chi\), and \(A_w^\chi\), then checked against
  the explicit \(4\times4\) matrices.
- The overlap caption gives \(\theta=40^\circ,30^\circ,20^\circ,10^\circ,0^\circ\)
  and \(N=4,6,8,10,12\); solver tolerances and raw point values are not supplied.
- Although the y-axis says “Overlap,” the plotted values equal the squared
  normalized inner products. This is fixed by all independently computed
  \(\theta=0\) points, not by a fitted scale.
- Exact diagonalization is performed inside fixed \(w\) sectors in the local
  Cartesian basis \(\{|S_x=0\rangle,|S_y=0\rangle,|S_z=0\rangle\}\). This is
  algebraically exact and avoids the \(3^N\) full-space Lanczos problem.
- The current implementation constructs periodic bonds. It cannot presently
  adjudicate V003-V005, so the open-boundary claim families are method gaps,
  not assumed consequences of the periodic checks.
- No existing runner expands the physical MPS back into the fractionalized
  singlet/triplet bond basis or constructs perturbative orders; V006-V007
  therefore remain uncovered rather than inferred from nearby phase data.
