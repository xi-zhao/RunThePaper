# Formula Verification

This document explains which formulas are allowed to feed numerical reproduction.

Machine-readable result:

```text
outputs/checks/formula_verification.json
```

Run:

```bash
python private validation harness/scripts/check_formula_gate.py case/<paper-id> --write
```

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| EQC001 | Confined mode spectrum | verified | Re-derived from Kummer termination and Dirichlet quantization; dimensions checked. |
| EQC002 | Landau-like energy | verified | Proper-time form and standard small-coupling plate limit checked. |
| EQC003 | Additional energy | verified | Re-derived from the mode sums; dimensional `alpha_0` correction recorded. |
| EQC004 | Bessel numerical form | verified | Obtained from two convergent geometric expansions and a standard Bessel integral identity. |
| EQC005 | Small-coupling limits | verified | `K_2` Landau and independently corrected `K_3` correction-sector limits derived. |
| EQC006 | Large-coupling limits | verified | Correct square-root exponential follows from the `K_1` argument. |
| EQC007 | Energy ratio | verified | Algebraic identity plus positivity and limiting checks. |

## Closed Or Unclear Formulas

| Formula | Reason | Numerical consequence |
| --- | --- | --- |
| Paper Eq. (26), second term | Lower limit is printed `n=1`, inconsistent with the original `n=0,1,...` sum and paper Eq. (34). | Use `n=0`; otherwise an unphysical extra `exp(-2 alpha_0 tau^2)` factor appears. |
| Paper Eq. (37) denominator | After `tau -> L tau`, dimensional `alpha` remains in one printed factor. | Use `alpha_0` in both factors. |
| Paper Eq. (39), last line | The printed exponent drops the square root in the `K_1` argument and its prefactor drops the standard `1/sqrt(x)`. | Use the preceding exact `K_1` expression and the corrected `exp[-2j sqrt(m_0^2+f alpha_0)]` asymptotic. |
| Paper Eq. (42) | Expanding both correction-sector denominators yields `tau^-7`, hence `K_3`, not the Landau-sector `tau^-5/K_2` integral. | Direct integrals and the independently derived Bessel series are used; the qualitative divergence remains. |

The machine gate is written by `check_formula_gate.py`; no numerical target is
run until that gate and the target-specific final-readiness gate pass.
