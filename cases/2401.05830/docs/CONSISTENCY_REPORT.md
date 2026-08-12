# Consistency Report

## 范围汇总

| 分类 | 数量 | 含义 |
| --- | ---: | --- |
| feature_match | 10 | 理论特征、参数与独立数值不变量通过；无作者数组可做逐点基准。 |
| blocked | 5 | 纯实验或实验后处理面板缺作者原始数据/完整方法输入。 |
| not_in_scope | 1 | Main Fig. 1 是装置与能级示意图。 |

## 理论目标

| Target | Paper item | 结论 | 关键证据 |
| --- | --- | --- | --- |
| T001 | Main Fig. 2 left | feature_match | affine residual `2.22e-16`; ellipse residual `6.66e-16` |
| T002 | Main Fig. 2 right | feature_match | strong root `0.0761974`; two slow-amplitude checks below `1e-14` |
| T003 | Main Fig. 4 theory | feature_match | coherent minimum `-0.0803284`; control minimum `+0.0010332` |
| T004 | Supp. Fig. 1 | feature_match | spectrum parity `4.97e-16`; bifurcation `gamma_b'=2` |
| T005 | Supp. Fig. 2 | feature_match | five loci and both bifurcation branches present |
| T006 | Supp. Fig. 3 | feature_match | 28/28 chords have slow component below `6.76e-16` |
| T007 | Supp. Fig. 4 left | feature_match | all three printed trajectories propagated |
| T008 | Supp. Fig. 4 right | feature_match | opposite slow-mode signs recovered |
| T009 | Supp. Fig. 5 left | feature_match | maximum root residual `1.10e-13` |
| T010 | Supp. Fig. 5 right | feature_match | peak advantage `0.0842247` |

## 实验目标的诚实边界

Main Fig. 3 top/bottom、Main Fig. 4 experimental series、Main Fig. 5 main/inset
均为 `missing_author_data`。代码没有把理论曲线冒充实验数据，也没有从原图恢复点列。

## 论文内部不一致

`DISC-RATE-FACTOR-TWO`：Main Eqs. (1)-(2) 的标准 dissipator 与 Supplement
Eqs. (1)-(4) 的 Bloch/Liouvillian 系数相差精确的两倍。三条独立检查均稳定复现该差异，
但在 fresh-context 审查和替代约定核查完成前，结论保持 `inconclusive`。

`DISC-HAMILTONIAN-PROSE-TWO`：实验段落写 `H=Omega sigma_x`，而 Main Eq. (1)、
补充材料和标准 Rabi 约定使用 `H=Omega sigma_x/2`。本次计算始终采用公式一致的后者。
