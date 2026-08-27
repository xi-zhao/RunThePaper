# Target Ledger

| Target ID | Paper item | Formula dependencies | Formula gate | Evidence state | Paper-scale implementation | Data / figure / checks | Review boundary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 2, both numerical-marker and analytic-line series | EQ001, EQ002, EQ003 | verified | historical paper-exact run attested | `main_figures_paper_scale`; config-ready, checkpoint/resume and CPU smoke passed | `outputs/data/fig2_charge_resolved.csv`; `outputs/figures/fig2_charge_resolved_reproduction.png`; `outputs/checks/target_checks.json` | `paper_supported`/completion still require fresh protocol-v2 review |
| T002 | Main Fig. 3, all-sector and six charge-sector numerical/analytic series | EQ001, EQ004, EQ005 | verified | historical paper-exact run attested | `main_figures_paper_scale`; 16 exact state shards, 4 analytic shards, aggregation/resume and CPU smoke passed | `outputs/data/fig3_spectrum_numeric.csv`; `outputs/data/fig3_spectrum_analytic.csv`; `outputs/figures/fig3_entanglement_spectrum_reproduction.png`; `outputs/checks/figure3_legend_audit.json` | printed-label conflict is `inconclusive`; no script may emit `paper_error_candidate` |

## T001 paper-parameter card

- Paper parameters: infinite half-filled tight-binding chain; subsystem
  `L=10000`; `K=1`; `Delta N_A=-5,...,5`; numerical lattice markers and
  no-fit analytic curves. Source: paragraph and caption immediately before/in
  Main Fig. 2.
- Historical generated parameters: exact paper values above, with 96 central
  modes whose window edges are saturated below `1e-13` and above `1-1e-13`.
- Rerun parameters: identical scientific parameters in
  `config/paper_scale.json`; the execution strategy changes only by adding
  checkpointed mode recurrence.
- Parameter match: `paper_exact` for the historical accepted run and declared
  paper-scale rerun; smoke artifacts remain `exploratory`.
- Machine acceptance: at least 4 logical CPUs, 16 GiB RAM, 3 GiB free disk,
  Python 3.11+ with 64-bit NumPy/SciPy BLAS/LAPACK. No accelerator required.
- Numerical acceptance: probability/entropy conservation, particle-hole and
  charge symmetry, active-mode convergence, and independent full-vs-subset
  eigensolver parity at the config thresholds.

## T002 paper-parameter card

- Paper parameters: same `L=10000`, half-filled `K=1` system; exactly 24
  closest-to-zero entanglement modes; all-sector and six displayed branches;
  ranks `1,...,1000`; horizontal range `x<=10`. Source: Eq. (11), surrounding
  text, and Main Fig. 3 caption.
- Historical generated parameters: exact paper-declared 24-mode enumeration;
  formula-derived branch identities `Delta N_A=0,...,5`.
- Rerun parameters: identical scientific object. The `2^24` integer occupation
  domain is partitioned into 16 canonical shards; each stores only its exact
  per-sector top-1000 candidates. Four independent x-grid shards evaluate the
  analytic curve before aggregation.
- Parameter match: `paper_exact` for the historical accepted run and declared
  paper-scale rerun; smoke artifacts remain `exploratory`.
- Machine acceptance: same shared eigenspectrum machine as T001. Shards may run
  sequentially on one 16-GiB CPU node or as a shared-filesystem job array.
- Numerical acceptance: exactly-once `2^24` coverage, streaming/monolithic
  parity, monotone sector onsets, 256-to-512 quadrature convergence, and the
  all-sector `I0` identity.

## Unplotted digital claim

The text after the critical Ising parity formula says it was “verified
numerically”, but supplies no lattice size, boundary conditions, numerical
method, tolerance, data, figure, or table. It is therefore not silently added
as a paper-exact figure target. The paper-scale smoke benchmark evaluates the
printed formula and checks exact sector-sum and scaling identities, while
`DIGITAL_CLAIM_AUDIT.md` records why the undisclosed author computation cannot
be reproduced as a paper-exact numerical artifact.

Main Fig. 1 is a nonnumerical schematic and is classified, not redrawn. The
full TeX bundle includes the Supplemental Material; it contains derivations but
no additional figures or numerical tables.
