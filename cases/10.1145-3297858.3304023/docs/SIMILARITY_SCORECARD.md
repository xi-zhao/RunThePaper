# 相似度评分卡：10.1145-3297858.3304023

## 总分

- Overall score: `61.71/100`
- Similarity level: `numerical_feature_reproduction`
- 解释：SABRE 的核心算法机制已经复现，小例子可以精确对齐；但 Table II 是论文里最重要的数值表，目前只达到部分一致。

## 单图/单表评分

| 数值图/表/面板 | Weight | 数值特征吻合度 | 关键数值接近度 | 原文目标覆盖度 | Score |
| --- | ---: | --- | --- | --- | ---: |
| Fig. 3 swap example | 1.0 | 50/50 - 论文小例子的 SWAP 决策和路由结构完全复现。 | 35/35 - CNOT 数、SWAP 数和深度都和论文例子一致。 | 13/15 - 这个解释性目标完整复现，但它不是全 benchmark corpus。 | 98 |
| Reverse traversal feature | 1.0 | 45/50 - 反向遍历改善初始映射的机制出现。 | 22/35 - 门数和深度趋势吻合，但不是论文全表的逐行数值。 | 8/15 - 覆盖了代表性 benchmark 特征，没有覆盖完整 Table II 精确条件。 | 55 |
| Decay trade-off | 1.0 | 44/50 - decay 带来的门数/深度 trade-off 出现。 | 20/35 - 趋势吻合，但缺作者实现细节导致逐行数值无法确认。 | 7/15 - 本地 sweep 能展示机制，但不是原文完整实验设置。 | 55 |
| Table II benchmark corpus | 4.0 | 35/50 - 输入 benchmark 和 SABRE 路由流程已经跑通，部分行体现优化效果。 | 8/35 - g_op 只有 7/26 逐行精确一致，是主要扣分来源。 | 13/15 - 26 行 benchmark 基本覆盖，但缺 seed、tie-breaking、BKA baseline 等关键条件。 | 56 |

## 结论

SABRE 的核心算法机制已经复现，小例子可以精确对齐；但 Table II 是论文里最重要的数值表，目前只达到部分一致。

这张评分卡的目标是让读者看到每一张数值图或表为什么得分，而不是只看到一个总分。

## 论文评测字段

| 数值图/表/面板 | Critical | Role | Parameter match | Artifact pass | Data-backed | Failure type |
| --- | --- | --- | --- | --- | --- | --- |
| Fig. 3 swap example | false | sanity_check | paper_exact | true | true | none |
| Reverse traversal feature | true | method_validation | proxy_model | true | true | partial_target_coverage |
| Decay trade-off | false | supporting | proxy_model | true | true | partial_target_coverage |
| Table II benchmark corpus | true | main_claim | paper_subset | true | true | numeric_mismatch |

说明：Table II 已经使用原文 26 个 benchmark 行和表格参数重跑；这里仍标为 `paper_subset`，是因为两个 benchmark 的 QASM qubit 元数据与论文表格不一致，并且作者的 seed/tie-breaking/BKA 细节没有公开。这个字段不是说我们只跑了 toy case，而是说严格完整复现所需的元信息仍不完整。
