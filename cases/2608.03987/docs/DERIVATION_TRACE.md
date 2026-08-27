# Derivation Trace

## Formula Lane Rule

The two numerical targets use only the paper's cost law and its explicitly
defined pipeline-gap metric. Both formulas are source-traceable and machine
gated in `EQUATION_CARDS.json` before any target is marked reproduced.

## EQ001 — realification arithmetic cost law

- **Source:** Theorem 1 and Eq. (8), TeX labels `thm:law` and `eq:law`.
- **Paper definitions:** a contraction step is a pass, ride, or merge. Their
  costs relative to the real skeleton are respectively 1, 2, and 3 real
  scalar multiplications per unit contraction volume.
- **Fractions:** `m` is the merge-volume fraction and `r` is the ride-volume
  fraction. The pass fraction is therefore `p = 1 - m - r`.
- **Derivation:**

  ```text
  overhead = 3m + 2r + 1p
           = 3m + 2r + (1 - m - r)
           = 1 + 2m + r.
  ```

- **Bounds:** non-negative volume fractions obey `m + r <= 1`. At fixed `m`,
  `r=0` gives the lower edge `1+2m`, while `r=1-m` gives the upper edge
  `2+m`. Consequently every point is inside `[1, 3]`.
- **Numerical use:** Figure 8 plots `(m, r)` computed from the clean-room final
  trees. Integer pass/ride/merge volumes are independently summed before the
  identity is evaluated.
- **Code:** `src/independent_tn.py::TreeStatistics`,
  `src/realified_figures.py::CostLawPoint`, and
  `src/realified_figures.py::validate_reproduction`.
- **Status:** verified; no open branch, sign, or convention ambiguity.

## EQ002 — relative pipeline gap

- **Source:** Figure 9 caption, TeX label `fig:pipe`.
- **Definition:**

  ```text
  gap = abs(o_convert_only - o_full_anneal) / o_full_anneal.
  ```

  Because independently optimized trees can have different real-skeleton
  volumes, this normalized overhead gap is not generally equal to the real-cost
  gap. The clean-room run therefore preserves the paper metric and separately
  audits `abs(C_convert-C_full)/C_full`.
- **Thresholds:** gaps at or below `1e-6` are aggregated at the left edge of
  panel (b); `5e-4` is the paper's acceptance line.
- **Numerical use:** Figure 9(a) plots three independently computed overhead
  ratios for 12 random circuits; Figure 9(b) applies the gap to all 67 circuits.
- **Code:** `src/realified_figures.py::PipelinePoint` and
  `src/realified_figures.py::validate_reproduction`.
- **Status:** source verified.
