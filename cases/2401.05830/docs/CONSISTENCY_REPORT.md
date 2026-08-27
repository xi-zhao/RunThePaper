# Consistency Report

## 范围汇总

| 分类 | 数量 | 含义 |
| --- | ---: | --- |
| covered | 27 items / 10 targets | 理论特征、参数与独立数值不变量通过；无作者数组可做逐点基准。 |
| uncovered | 2 claims | 两处因子 2 的论文内部一致性问题已检出，但尚未由 fresh-context 评审裁决。 |
| excluded experiment | 9 items | 论文实验测量或其后处理，保留在清单中但不进入理论复现分母。 |
| excluded schematic | 3 items | Main Fig. 1 的三个装置、能级与脉冲序列示意区域。 |

统一指标为 `27/29 = 93.10%` coverage；已覆盖 item 平均 fidelity 为 90.0，
所以整篇 reproduction degree 为 83.79。

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

## 实验测量的诚实边界

9 个实验 item 分布在 Main Fig. 2 左图的三组测量点、Main Fig. 3 top/bottom、
Main Fig. 4 的 raw/smoothed 两条实验序列、Main Fig. 5 main/inset。它们统一标记为
`experimental_measurement + excluded`：代码没有把理论曲线冒充实验数据，也没有从
原图恢复点列。

## 未覆盖 item 的因果归因

| Item / target | 直接原因 | 根本原因 | 代码错误判断 | 下一项判别测试 |
| --- | --- | --- | --- | --- |
| `claim_dissipator_rate_factor_two` / T011 | Main Eqs. (1)-(2) 的标准 dissipator 与 Supplement Eqs. (1)-(4) 的 Bloch/Liouvillian 系数相差精确两倍 | `unresolved`：正文漏写因子 2 与未声明的速率约定尚不能区分 | `not_found_after_checks`：算符重推、独立 4x4 实现、单元测试三路一致 | fresh-context 评审重推并检查正式版本和勘误 |
| `claim_hamiltonian_prose_factor_two` / T012 | 实验段写 `H=Omega sigma_x`，方程统一使用 `H=Omega sigma_x/2` | `unresolved`：文字笔误与局部 Rabi 频率重定义尚不能区分 | `not_applicable`：这是两个印刷陈述的冲突，runner 没有第二条执行路径 | fresh-context 评审追踪全文定义并检查正式版本和勘误 |

两项当前都保持 `inconclusive`，不能提前宣布论文错误；但它们已经进入分母并以 0 分
计入整篇复现度。
