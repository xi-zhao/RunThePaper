# Target Ledger

| Target | Paper item | Scientific object | Formula refs | Parameter status | Current state | Data |
| --- | --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 1(d) | moire potential | EQ001 | paper physical parameters | physically_consistent | `outputs/data/T001_main_fig1d_potential.npz` |
| T002 | Main Fig. 2(a) | bands + TB fit | EQ002, EQ003 | paper physical parameters | physically_consistent | `outputs/data/T002_main_fig2a_bands.npz` |
| T003 | Main Fig. 2(b) | DOS/filling | EQ002, EQ006 | reduced result; paper-scale code ready | physically_consistent | `outputs/data/T003_main_fig2b_dos.npz` |
| T004 | Main Fig. 2(c) | Wannier orbital | EQ002, EQ004 | reduced result; paper-scale code ready | physically_consistent | `outputs/data/T004_main_fig2c_wannier.npz` |
| T005 | Main Fig. 2(d) | hopping sweep | EQ002, EQ003 | reduced result; paper-scale code ready | physically_consistent | `outputs/data/T005_main_fig2d_hopping.npz` |
| T006 | Main Fig. 3(a) | screened interactions | EQ004, EQ005 | reduced result; paper-scale code ready | physically_consistent | `outputs/data/T006_main_fig3a_interactions.npz` |
| T007 | Main Fig. 3(b) | exchanges | EQ003, EQ005, EQ007 | reduced result; paper-scale code ready | physically_consistent | `outputs/data/T007_main_fig3b_exchange.npz` |
| T008 | Main Fig. 4(a) | Fermi contour | EQ002, EQ008 | reduced result; paper-scale code ready | physically_consistent | `outputs/data/T008_main_fig4a_fermi_contour.npz` |
| T009 | Supp. Fig. 5(a) | mismatch potential | EQ001, EQ009 | paper physical parameters | physically_consistent | `outputs/data/T009_supp_fig5a_potential.npz` |
| T010 | Supp. Fig. 5(b) | mismatch bands + TB | EQ002, EQ003, EQ009 | paper physical parameters | physically_consistent | `outputs/data/T010_supp_fig5b_bands.npz` |
| T011 | Supp. Fig. 5(c) | mismatch hopping sweep | EQ003, EQ009 | reduced result; paper-scale code ready | physically_consistent | `outputs/data/T011_supp_fig5c_hopping.npz` |
| T012 | Supp. Fig. 5(d) | mismatch interactions | EQ004, EQ005, EQ009 | reduced result; paper-scale code ready | physically_consistent | `outputs/data/T012_supp_fig5d_interactions.npz` |
| D001 | Main Fig. 1(c) | displacement DFT map | — | missing benchmark metadata | blocked | none |

Generated figure and comparison paths are assigned one-to-one using the same target ID.
No target is covered by a different panel, composite, or source-image extraction.

`paper-scale code ready` means the sharded computation, configuration, run contract,
expected outputs and machine-verifiable acceptance rules exist. It does not mean that
the full campaign ran or that the target is paper-exact.

## Coverage contract

- eligible reproduction items: 13;
- covered by independent numerical artifacts: 12;
- uncovered: `D001` only;
- coverage: **92.31%**.

`D001` has a zero item score and is excluded from the historical 70-point target
average only because no generated primary metric exists. It is still included as zero
in the paper-level reproduction degree. Its direct cause is unavailable indispensable
first-principles input; its confirmed root cause is publication underspecification.
Code fault is not applicable before the missing DFT contract is uniquely defined.
The next discriminating action is to freeze a citable DFT input contract and execute an
independent convergence study without author numerical code.
