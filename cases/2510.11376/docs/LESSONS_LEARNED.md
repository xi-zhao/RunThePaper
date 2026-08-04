# Lessons learned

## New Failure Modes

1. A one-character coefficient change can change a nonempty codimension-two
   manifold into the empty set; denominator clearing should precede numerical
   optimization.
2. Repairing the transcription typo is not enough: the frozen optimizer also
   misses a continuous exact zero family and selects a singular crossing.
3. A physical quantity named `g^(2)` is not automatically nonnegative if the
   printed closed form contains a typo. Test the supplied formula literally.
4. GPU scale is downstream of formula validity. Exact local algebra saved an
   unnecessary A100 campaign.

## Reusable Checks Or Tools

- `waveguide_gold.py` provides reusable rational-denominator clearing,
  analytic amplitude Jacobians, and an exact asymptotic counterexample path.
- The workflow now treats a claimed constrained optimum at a symmetry-branch
  collision as a mandatory rank-check trigger.
