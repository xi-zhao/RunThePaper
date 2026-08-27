# Target Ledger

| ID | Paper item | Formula dependencies | Gate | Status | Planned data / figure |
| --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 1(a,b), 2 directional energy items | EQ001-EQ003 | open | runnable | `main_fig1_levels.csv`, `main_fig1_levels.png` |
| T002 | Main Fig. 2 | EQ001-EQ006, EQ008 | open | runnable | `main_fig2_correlations.csv`, `main_fig2.png` |
| T003 | Main Fig. 3(a-c), 5 atomic items | EQ001-EQ008 | open | runnable | `main_fig3_correlations.csv`, `main_fig3_distributions.csv`, `main_fig3_abc.png` |
| T004 | Main Fig. 3(d), 2 directional energy items | EQ001-EQ003 | open | runnable | `main_fig3_levels.csv`, `main_fig3d.png` |
| T005 | Main Fig. 4(a-c), 5 atomic items | EQ001-EQ008 | open | runnable | `main_fig4_correlations.csv`, `main_fig4_distributions.csv`, `main_fig4.png` |
| T006 | Supplement Fig. S1 | EQ001, EQ003 | open | runnable | `supp_fig_s1_fizeau.csv`, `supp_fig_s1.png` |
| T007 | Supplement Fig. S2 | EQ002 | open | runnable | `supp_fig_s2_levels.csv`, `supp_fig_s2.png` |
| T008 | Supplement Fig. S3, 16 directional level items | EQ001-EQ003 | open | runnable | `supp_fig_s3_levels.csv`, `supp_fig_s3.png` |
| T009 | Supplement Fig. S4, 8 atomic items | EQ002-EQ008 | open | runnable | `supp_fig_s4_*.csv`, `supp_fig_s4.png` |
| T010 | Supplement Fig. S5, 8 atomic items | EQ002-EQ008 | open | runnable | `supp_fig_s5_*.csv`, `supp_fig_s5.png` |
| T011 | Supplement Fig. S6, independent g2/g3 families | EQ002-EQ006, EQ008 | open | runnable | `supp_fig_s6_analytic_numeric.csv`, `supp_fig_s6.png` |
| T012 | Supplement Fig. S7(a,b), 2 directional items | EQ001-EQ006, EQ008 | open | runnable | `supp_fig_s7_rotation_sweep.csv`, `supp_fig_s7.png` |
| T013 | Supplement Fig. S8 | EQ001-EQ006, EQ008 | open | runnable | `supp_fig_s8_6p6khz.csv`, `supp_fig_s8.png` |
| T014 | Supplement Fig. S9, 6 atomic items | EQ001-EQ008 | open | runnable | `supp_fig_s9_*.csv`, `supp_fig_s9.png` |
| T015 | Supplement Table S2 | EQ001-EQ007 | open | runnable | `supp_table_s2_cases.csv`, `supp_table_s2_check.json` |

The atomic inventory contains 62 eligible theory items, all bound to T001-T015.
This is a coverage statement, not a claim of perfect fidelity or lifecycle
completion: every item inherits the current evidence quality of its target and
will be re-adjudicated target-by-target in W2.

## Shared paper-parameter card

- `lambda=1550 nm`, `radius=30 um`, `n0=1.4`, `n2=3e-14 m2/W`,
  `Veff=150 um3`, `Q=5e9`.
- Weak drive: `Pin=2 fW`; stronger drive: `Pin=0.3 pW`.
- Rotation values: `Omega=0, 6.6, 15, 29, 30, 45, 58 kHz` as used by the
  corresponding source panels.
- Exact Hamiltonian, single-photon loss model and direction sign match the
  paper. The unstated numerical curve density is an implementation resolution,
  not a substituted physical parameter.
- `parameter_match=paper_exact` for all T001-T015.
- `artifact_stage=final_reproduction` after isolated-run and convergence checks
  pass; prior workspace probes remain exploratory.
- `generated_data_provenance=independent_numerics` for master-equation targets
  and `analytic_reference` for formula-only energy/Fizeau targets.

## Per-target display ranges and evaluation points

- T002: `k=0..3`, with the paper-highlighted `k=1.5` probe.
- T003/T004: `k=2..3`, zoom `2.48..2.52`, distributions and levels at `k=2.5`.
- T005: `k=0.8..2.2`, zoom `1.48..1.52`, distributions at `k=1.5`.
- T006: `Omega=0..60 kHz`.
- T009: weak-drive nonspinning sweep covering `k=0..2.5`, distributions at
  `k=1` and `k=2`.
- T010: strong-drive nonspinning sweep covering `k=0..3.5`, distributions at
  `k=1`, `k=2`, and `k=3`.
- T011: nonspinning analytic/numeric comparison over `k=0.5..3.5`.
- T012: both shift signs over `k=0..3` for `Omega=0,15,30,45 kHz`.
- T013: `k=0..3` for `Omega=0` and both signs at `6.6 kHz`.
- T008/T015: all eight Supplement Table S2 configurations are derived from
  `E_n=0`, hence `k=n+s|Delta_F|/U`. The four allowed rows have the same
  required `k` for both directions; the four prohibited rows have different
  required `k` values and therefore cannot share one laser detuning. Level
  schematics use the paper's exact ideal ratios `|Delta_F|/U=1` or `1/2`;
  master-equation curves use the printed, rounded `Omega=58` or `29 kHz`.
- T014: source-declared `Omega=58 kHz` cases at `k=2,3` and `Omega=29 kHz`
  cases at `k=1.5,2.5`.
