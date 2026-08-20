# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 3 | 三个数值图的公式、参数、独立方法和科学区域渲染全部通过。 |
| feature_match | 0 | 没有只停留在特征级的目标。 |
| partial_match | 0 | 没有局部通过目标。 |
| blocked | 1 | Sec. VII `n=11,17` 的通用计算代码已就绪，但定量趋势缺少不可替代的论文输入。 |
| not_in_scope | 1 | Main Fig. 1 为概念示意图。 |

## Per-Target Consistency

| Target | Paper item | Level | Scientific evidence | Pixel score | Difference |
| --- | --- | --- | --- | ---: | --- |
| T001 | Main Fig. 2 upper | exact_match | projector vs Eq. (23): `1.11e-16`; exact threshold and quadratic limit | 99.6531 | 仅栅格化/字体抗锯齿 |
| T002 | Main Fig. 2 lower | exact_match | projector vs Eq. (22): `8.33e-17`; endpoints and monotonicity pass | 99.7807 | 仅栅格化/字体抗锯齿 |
| T003 | Main Fig. 3 | exact_match | codeword enumerator vs Eq. (36): `1.67e-16`; exact threshold and cubic limit | 99.6574 | 仅栅格化/字体抗锯齿 |

## Quantitative Claims

- T threshold error: `0.17267316464601146`; fidelity `0.9095750850556475`; polarization `0.6546536707079771`.
- H threshold error: `0.14148029265616752`; fidelity `0.9265633854970918`; polarization `0.717039414687665`.
- Stabilizer lower bounds: T `0.8880738339771153`; H `0.9238795325112867`.
- Resource exponents: `xi_T=0.2037950471`, `xi_H=0.4056838711`, `gamma=2.4649735207`.

## Blocked Publication Claim

Direct cause: Sec. VII does not identify the actual `n=11,17` GF(4) codes, search space, acceptance rule or numerical thresholds.

Root cause: the publication records a qualitative exploratory statement without the indispensable numerical specification. This is not a compute shortage. The generic implementation is independently validated against the published five-qubit map, so the remaining block is not an observed reproduction-code defect.

Code status: `gf4_codes.py` enumerates signed stabilizer/logical cosets, `run_gf4_campaign.py` provides the executable campaign, and `run_contract.gf4.json` fixes resources and outputs. The empty code list is intentional and fail-closed; filling it with guessed codes is forbidden.

Next discriminating evidence: author-supplied generator matrices or a citable exact search protocol plus the reported per-code outputs. Without one of these, inventing a search would create a new study rather than reproduce the printed computation.

## Paper Review

All printed formulas, thresholds, limiting coefficients and curve semantics checked in the executable scope are internally consistent. No paper-error candidate is emitted. Fresh-context protocol-v2 review remains required before lifecycle completion.
