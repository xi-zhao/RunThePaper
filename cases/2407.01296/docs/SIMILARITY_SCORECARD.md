# Similarity Scorecard

当前归一化总分为 **73.09/100**，层级为 `numerical_feature_reproduction`。这个分数同时受科学特征、数值接近度、面板覆盖和证据等级约束；不是单纯像素分。

| Target | Score | Level | 解释 |
| --- | ---: | --- | --- |
| T001 Main Fig. 2(a-c) | 90.0 | complete_reproduction | paper-exact 独立数据；像素严格门槛未通过 |
| T002 Main Fig. 4(a-f) | 80.0 | numerical_feature_reproduction | 六面板通过；含未公开重建选择 |
| T003 Main Fig. 3(a-b) | 80.0 | numerical_feature_reproduction | 独立 GBZ 子集 |
| T004 Main Fig. 2(d) | 60.5 | numerical_feature_reproduction | 缩小尺度区域收敛通过 |
| T005 Supplement S2 | 67.5 | numerical_feature_reproduction | exact/Amoeba 密度相关 0.9731 |
| T006 Supplement S4 | 65.5 | numerical_feature_reproduction | 归一化与绕数检查通过 |
| T007 Supplement S5 | 55.5 | feature_not_accepted | 数值正确，但关键选态能量未公开且 paper run 未执行 |
| T008 Supplement S6 | 70.0 | numerical_feature_reproduction | 普通/临界绕数符号结构通过 |
| T009 Supplement S7 | 52.5 | feature_not_accepted | 公式通道通过，但论文标量语义与几何不唯一 |

T007/T009 的低分不是实现失败：两者都有代码、生成数据和科学断言；它们没有被强行提分，是因为论文缺失输入或语义仍需证伪。权威机器记录见 `outputs/checks/similarity_scorecard.json`。
