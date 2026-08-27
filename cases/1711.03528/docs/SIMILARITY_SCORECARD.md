# 相似度评分卡：1711.03528

## 总分

- Overall score: `70.10/100`
- Similarity level: `numerical_feature_reproduction`
- 解释：量子多体 scar 的核心数值特征和 `L=28` 同一对称 sector 已复现；`L=32` 与 bond-400 MPS 路径已有代码，但尚未执行论文尺度收敛网格。

## 单图评分

| 数值图/表/面板 | Weight | 数值特征吻合度 | 关键数值接近度 | 原文目标覆盖度 | Score |
| --- | ---: | --- | --- | --- | ---: |
| Fig. 1 Hamiltonian graph | 0.5 | 50/50 - `L=6` Fibonacci basis 和 PXP 连接结构复现。 | 32/35 - 节点数和边规则一致，布局不要求完全相同。 | 9/15 - 覆盖模型结构图，不是主数值结论。 | 90 |
| Entanglement dynamics | 1.2 | 46/50 - `Z2` 慢纠缠增长、局域振荡、revival 都出现。 | 26/35 - 振荡周期 `2.375` 接近论文 `~2.35`。 | 7/15 - 本地 finite-size ED，不是 iTEBD thermodynamic limit。 | 70 |
| Fig. 3 scar tower / FSA | 1.5 | 46/50 - `L=28` 同一对称 sector 出现完整 15 态 scar tower。 | 27/35 - tower spacing 相对标准差 `0.104`，能量对称且小尺寸 sector 精确性通过测试。 | 11/15 - 同一 `k=0, I=+1` sector 已完成到 `L=28`；论文为 `L=32`。 | 70 |
| Fig. 4 level statistics | 0.8 | 42/50 - 已完成对称性分解、去零模和 unfolding，分布呈 WD 而非 Poisson。 | 24/35 - `r=0.497`，更接近 GOE `0.531`；Wigner L1 距离小于 Poisson。 | 7.5/15 - 主图和 DOS inset 均为同一对称 sector 的缩小尺度复现。 | 70 |

## 结论

这个 case 已经展示论文的主要物理机制，并完成 `L=28` 的严格 `k=0, I=+1` sector 与 unfolding。剩余边界是两个已实现但未执行的论文尺度任务：`L=32` dense ED 与 bond-400 MPS 收敛网格。

## 论文评测字段

| 数值图/表/面板 | Critical | Role | Parameter match | Artifact pass | Data-backed | Failure type |
| --- | --- | --- | --- | --- | --- | --- |
| Fig. 1 Hamiltonian graph | false | method_validation | paper_exact | true | true | none |
| Entanglement dynamics | true | main_claim | reduced_scale | true | true | insufficient_compute |
| Fig. 3 scar tower / FSA | true | main_claim | reduced_scale | true | true | none |
| Fig. 4 level statistics | false | supporting | reduced_scale | true | true | none |
