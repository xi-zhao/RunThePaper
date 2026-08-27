# Similarity Scorecard: 2605.25398

## 量化结果

- 目标加权相似度：`85.3/100`
- 原子 item 覆盖率：`100%`（`20/20`）
- 已覆盖 item 平均 fidelity：`85.0/100`
- 复现度：`85.0/100`，等级 `quantitative_reproduction`
- 最终处置：`20 reproduced / 0 externally blocked / 0 attempted-not-reproduced / 0 pending`

主指标只评价可复现的理论数值 item，不把实验红点、芯片照片或示意图塞进分母。视觉相似度不进入科学复现度；它是后续独立的渲染诊断。

| Target | Feature | Numeric | Scope | Final score |
| --- | ---: | ---: | ---: | ---: |
| T001 Fig. 2g-h theory distributions | 44/50 | 24/35 | 12/15 | 80 |
| T002 Fig. 3 PT/entropy/SFF | 49/50 | 30/35 | 13/15 | 89 |
| T003 Fig. 4 OTOC/PR | 48/50 | 29/35 | 13/15 | 80 |
| T004 Fig. S1 conditional PT | 50/50 | 32/35 | 13/15 | 90 |
| T005 Fig. S4 scaling | 49/50 | 29/35 | 13/15 | 89 |
| T006 Fig. S5 all OTOCs | 46/50 | 27/35 | 13/15 | 80 |
| T007 Fig. S6 powers/FFT | 49/50 | 31/35 | 13/15 | 89 |

所有 target 都使用论文公开的科学参数合同；随机种子和未公开绘图网格被明确建模为随机矩阵集合/连续时间的独立代表，而不是偷取作者实例。分数上限仍保守反映没有作者逐点曲线和实验计数，不能理解成数据缺失阻止了科学复现。

机器权威记录：`outputs/checks/similarity_scorecard.json`。
