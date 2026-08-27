# Paper Map

## Paper

- PaperID: `1608.02589`
- Title: *Discrete time crystals: rigidity, criticality, and realizations*
- Authors: Norman Y. Yao, Andrew C. Potter, Ionut-Dragos Potirniche, Ashvin Vishwanath
- arXiv: <https://arxiv.org/abs/1608.02589>
- Journal reference: Phys. Rev. Lett. 118, 030401 (2017)
- Publication DOI: `10.1103/PhysRevLett.118.030401`

## Raw Materials

- `raw/paper.pdf`: arXiv PDF.
- `raw/paper.txt`: extracted PDF text.
- `paper-source/source.tar`: arXiv source bundle.
- `paper-source/extracted/Discrete_Time_Crystal_PRL_Maintext_v89.tex`: main TeX source.
- `paper-source/extracted/Discrete_Time_Crystal_SI_v8.tex`: supplementary TeX source.
- `internal-paper-reference/`: rendered original figures from TeX source.

## Main Question

The paper studies a driven disordered spin chain that spontaneously doubles the period of the drive. The numerical goal is to show that interactions and localization turn a fragile spin-echo oscillation into a rigid subharmonic response at half the drive frequency.

## Model

The binary Floquet drive is:

```text
H1 = (pi/2 - epsilon) sum_i sigma_i^x
H2 = sum_i J_i^z sigma_i^z sigma_{i+1}^z + B_i^z sigma_i^z
U_f = exp(-i H2) exp(-i H1)
```

The paper uses maximal disorder `W = 2 pi`, coupling disorder `J_i^z in [J_z - 0.2 J_z, J_z + 0.2 J_z]`, and scans interaction strength `J_z` and pulse imperfection `epsilon`.

## Reproduction Scope

This case implements a local small-size exact simulation of the same Floquet model. It reproduces the key numerical features:

- noninteracting spins drift away from the half-frequency peak when `epsilon` is nonzero;
- interacting disordered spins keep a peak locked near half the drive frequency;
- level-statistics data and peak-variance data can be generated from exact diagonalization / time evolution;
- long-range interactions also show a variance peak as `epsilon` is scanned.

The legacy case does not reproduce the full PRL-scale disorder campaign. A later migration now provides executable coverage for all 38 numerical items in the paper and supplement, including resumable paper-scale configuration and aggregation. The full campaign has not run, so larger-system phase boundaries, critical scaling, and supplementary 1000-period spectra remain compute/review blockers rather than completed results.
