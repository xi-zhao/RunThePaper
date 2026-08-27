# Consistency Report

## Consistent Features

| Feature | Paper | Local result | Status |
| --- | --- | --- | --- |
| Batch probability histogram | `Np` follows Porter-Thomas exponential line | `Np` follows the same exponential line | Consistent |
| Full fixed-subspace XEB | Close to zero for the full enumerated subspace | `0.00494` for depth 20, `-0.00252` for depth 14 | Consistent |
| Post-selected XEB | Higher when selecting top-probability bitstrings | Monotone decreasing as selected fraction grows; top 10% around `2.3` | Consistent |
| Conditional probabilities | Normalize and follow Porter-Thomas | Normalize to `1.0` and follow Porter-Thomas | Consistent |
| Head contraction dominance | `T_head` dominates `T_tail` | `T_tail/T_head ≈ 6.36e-4` from table values | Consistent |

## Partial Or Not Exact

| Item | Reason |
| --- | --- |
| Exact Fig. 2 raw bars | Original bars come from 53-qubit Sycamore contraction over `2^21` bitstrings. Local case uses an 18-qubit random circuit. |
| Exact Fig. 5 raw bars | Same scale limitation. |
| Exact Fig. 6 raw bars | Same scale limitation. |
| Table III bitstring amplitudes | Requires exact full-scale Sycamore contraction; now recorded as `planned_large_scale`. |
| GPU timing claims | Require the original hardware and contraction code path; now recorded as external-required. |

## What The Case Proves

The case proves that the paper's formula-to-observable chain can be followed and executed:

```text
fixed closed bits
-> enumerate open bits
-> probability batch
-> XEB
-> Porter-Thomas histogram
-> conditional probability distribution
```

## What It Does Not Prove

It does not prove the authors' 53-qubit performance claim on this local machine. That claim is a hardware-scale reproduction target.

To upgrade this case, the harness should add a "large-scale target mode" that separates:

- formula and observable reproduction;
- author data validation;
- exact large-scale rerun;
- hardware-performance reproduction.
