# Paper Map

## Identity

- **Preprint:** arXiv:2608.05312v1 (2026-08-05)
- **Formal publication:** unpublished as of 2026-08-08
- **Frozen source:** `../raw/paper.pdf`, `../raw/arxiv-2608.05312v1-source.tar.gz`
- **Primary TeX:** `../paper-source/main_PRL_v2_PNEdited.tex`

## Scientific claim

The paper proposes a non-Condon phonon-emission jump

```text
site excitation -> cavity photon -> sink
```

that removes population from the dark manifold without a reverse channel at
zero temperature. Its total dark-to-bright escape rate is fixed by the unit
sum of photonic weights, rather than diluted by the number of dark states.

## Section and equation map

| Source | Content | Case formula card |
| --- | --- | --- |
| Main Eq. (1), `eq:H` | Tavis-Cummings-Hubbard Hamiltonian with hopping disorder | EQ001 |
| Main Eq. (2), `eq:rates`; SM Eq. (S4) | emission/absorption bath rates | EQ002 |
| Main Eq. (3), `eq:Lrec`; SM Eq. (S5) | rescue and finite-temperature reverse jumps | EQ003 |
| Main Eq. (4), `eq:rescue` | eigenstate transition rate and photonic sum rule | EQ004 |
| Main Eq. (5); SM Eqs. (S10)-(S16) | lumped populations and two-exponential efficiency | EQ005 |
| SM Eq. (S19) | column-vectorized Liouvillian and direct propagation | EQ006 |
| SM Appendix E | two-largest-photonic-weight bright projector | EQ007 |

## Numerical inventory

| Paper item | Type | Core observable | Case decision |
| --- | --- | --- | --- |
| Fig. 1(a,b) | schematic | non-Condon mechanism | excluded from numerics |
| Fig. 1(c) | numerical | optimized peak efficiency versus N | T001 |
| Fig. 2(a,b) | numerical | dark and sink population dynamics | T002 |
| Fig. 2(c,d) | numerical | bright/dark/cavity/sink populations | T003 |
| Fig. 3(a-c) | numerical | finite-temperature competition | T004 |
| Fig. S1(a,b) | numerical | site-N drain rate sweep and no-dissipation baseline | T005 and T012 |
| Table S1 | numerical | seven transport regimes | T006 |
| Table S2 | numerical | coherent-detuning robustness | T007 |
| Fig. S2(a,b) | numerical | size-gap logarithmic/power-law fits | T008 |
| Fig. S3(a,b) | numerical | site-N manifold dynamics | T009 |
| Fig. S4 | numerical | N=64 finite-temperature map | T010 |
| Fig. S5 | numerical | four QCLE-versus-Lindblad benchmark series | T011, all four source-blocked |

The atomic inventory contains 74 displayed items. Two Fig. 1 schematics are
excluded, leaving 72 eligible scientific numerical items: 68 covered and four
uncovered (coverage `94.44%`). The uncovered set is exactly the four Fig. S5
series; see `figure_coverage.json` for every item.

## Parameter evidence and reconstruction

Directly stated parameters include `g=1.5 meV`, `delta_t=0.5 meV`,
`gamma_lead=0.5 meV`, the channel rates, measurement times, system sizes, and
15--25 disorder realizations. The coherent simulations are at cavity resonance.

The following claim-relevant values are not explicitly printed in arXiv v1:

- mean hopping `t`;
- the exact loaded source state;
- random seeds;
- most rate grids and temperature grids;
- the project-repository URL promised in Appendix H.

This case reconstructs `t=1 meV` because SM Fig. S5 locates the QCLE/Lindblad
peak near `g=t` and its axis uses that unit. It reconstructs the initial state
as `|1><1|`, consistent with the pump schematic, the phrase “loaded at the
source”, and the plotted initial dark fraction. The reconstruction is strongly
cross-checked: with these choices, independent seeds 0--14 give the Fig. 2
N=6 dephasing efficiency 0.796 (paper 0.794--0.799) and the Fig. 3 N=6/N=64
dephasing efficiencies 0.662/0.093 (paper about 0.66/0.09).

Because author seeds and exact grids remain unavailable, no generated artifact
is labeled `paper_exact` or `final_reproduction`. Figure S5 has a stricter
boundary: its benchmark operating inputs are missing from the publication, so
neither source pixels nor author numerical code may be used to manufacture an
independent scientific result.
