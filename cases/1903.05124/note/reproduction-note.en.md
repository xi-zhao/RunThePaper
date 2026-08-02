# Quantum error correction in scrambling dynamics: numerical reproduction

This package reproduces the theory-numerical content of Choi, Bao, Qi, and
Altman, *Quantum Error Correction in Scrambling Dynamics and
Measurement-Induced Phase Transition*, Phys. Rev. Lett. **125**, 030505
(2020). It is a scientific reproduction, not image tracing: the derivations,
Clifford/stabilizer dynamics, frame-potential estimator, and finite-size fits
produce all numerical arrays independently. Paper pixels are used only in the
final comparison boards.

## Scope and result

All 44 visible theory-numerical panels and insets are covered across Main
Fig. 2(b–e) and Supplement Figs. S2–S6. Circuit, channel, and tensor-network
schematics are not treated as numerical targets. Twenty items are reproduced
at paper scale: all four S2 frame-potential panels at `n=22`, 22 depths, and
50,000 samples per depth, plus all sixteen S3 subpanels at `L=32`, `m=11`, and
240 trajectories per setting. The remaining 24 items have independent
feature-scale evidence with reduced sizes or statistics and are labeled as
such.

The scientific audit score is **78.41/100**. T001, T002, T003, T004, and T006
score 80; T005 scores 70 because its transition locations pass while the
depth-independence of the fitted critical exponent remains only partially
supported at `L<=24`. The downstream presentation score is **68.30/100**; it
does not contribute scientific credit.

Key numerical evidence includes paper-scale approach to the Haar moments for
`k=1,2,3`, a late-depth `F4=29.00±0.85` whose 95% lower bound remains above 24,
the strong-scrambling measurement-protection signature, and independently
fitted transition probabilities with mean absolute errors of `0.00409` (Main
Fig. 2) and `0.00484` (S5) against the published summary table. The S6 campaign
uses all six paper block sizes and exact `d/m=3`, while retaining the explicit
`L<=24` precision boundary.

## Run and inspect

From the repository root:

```bash
python -m unittest discover -s cases/1903.05124/code/tests -v
python cases/1903.05124/code/scripts/run_supp_fig_s2.py --render-only
python cases/1903.05124/code/scripts/run_supp_fig_s3.py --render-only
python cases/1903.05124/code/scripts/run_supp_fig_s4.py \
  --refinement-input cases/1903.05124/outputs/data/supp_fig_s5_refinement_numerical_data.csv
python cases/1903.05124/code/scripts/run_supp_fig_s5.py \
  --refinement-input cases/1903.05124/outputs/data/supp_fig_s5_refinement_numerical_data.csv
```

The simulation runners also expose `--scale smoke` for a fresh fast run and
larger feature/paper modes where implemented. A fresh run writes structured
CSV/NPZ data and JSON checks before rendering PNG figures.

The public package contains no paper PDF, standalone original figure, or
digitized source curve. See the [equation derivation](../docs/DERIVATION.md),
[method trace](../docs/METHOD_TRACE.md), and
[score interpretation](../docs/SIMILARITY_SCORECARD.md).
