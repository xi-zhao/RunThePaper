# Method Trace

## MTH001 - closed aggregate/individual test

- Source: Sections II.B-III and Eqs. 9-21.
- Role: shared detection and quantification algorithm.
- Inputs: aligned circuit count tables from `C` contexts and comparison-level
  significance `alpha`.
- Outputs: per-circuit LLR/p-value, aggregate LLR/p-value/`N_sigma`, Hochberg
  pseudo-threshold, significant circuits, JSD, TVD, and SSTVD.
- Steps:
  1. validate identical circuit identities and positive pool totals;
  2. compute each multinomial G-test LLR and Wilks p-value;
  3. test the aggregate at `alpha/2`;
  4. choose `beta=alpha` after aggregate detection, otherwise `alpha/2`;
  5. apply Hochberg to the individual p-values;
  6. quantify JSD for all circuits and TVD/SSTVD for two-context comparisons.
- Code: `scripts/reproduce_context_dependence.py::analyze_contexts`.
- Checks: paper's two single-circuit examples, LLR/JSD identity, Hochberg rank
  self-consistency, and aggregate degree-of-freedom additivity.
- Status: `verified`.

## MTH002 - Fig. 2 five-pool LSGST reanalysis

- Source: Section IV, Appendix A, `anc/Fig2.ipynb`, and
  `anc/Simulated_data/ds_linear_{0..4}.txt` inside the frozen bundle.
- Role: reproduce all Fig. 2 numerical content.
- Inputs: 1405 identical circuits, 100 shots per circuit in each of five time
  periods, and global significance 5% split over 11 top-level comparisons.
- Outputs: ten pairwise comparisons, the joint five-context comparison, and
  the pass-1/pass-5 circuit-length distributions.
- Core-length rule: use the first LSGST generation in which a deduplicated
  circuit appears; parenthesized repetitions map to the smallest power-of-two
  generation that can contain their expanded germ, with bare repetitions in
  the initial generation.
- Checks: 1405 unique aligned circuits, all 100-shot pools, the complete Fig. 2
  upper matrix, joint `N_sigma`, 21 joint ICT detections, 25 pass-1/pass-5 ICT
  detections, and growth of upper-tail discrepancy with length.
- Status: `verified`.

## MTH003 - Fig. 3 IBM LGST reanalysis

- Source: Section V, Appendix A, `anc/Fig3.ipynb`, fiducial lists, and all
  `anc/IBM_data/` files inside the frozen bundle.
- Role: reproduce the seven displayed max-SSTVD values and drift controls.
- Inputs: the deduplicated 40 LGST circuits formed from the released
  preparation/measurement fiducials and `{Gi,Gh,Gs}`; 1024 shots per circuit
  and context; seven rung comparisons; 5% significance split over 14 tests.
- Outputs: before/after drift decisions and before/during crosstalk statistics
  for each rung.
- Checks: generated LGST set equals the first 40 author-file circuit set, every
  selected pool has 1024 shots, no drift comparison detects inconsistency, all
  crosstalk comparisons do, and all seven max SSTVD values match the released
  notebook exactly.
- Boundary: this is an independent statistical reanalysis of historical IBM
  data, not a rerun on the retired `ibmqx3` device.
- Status: `verified`.
