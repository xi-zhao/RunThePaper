# Consistency Report

## 汇总

| 类别 | 数量 | 含义 |
| --- | ---: | --- |
| paper-exact scientific pass | 8 | T001–T007、T011 的公式、参数和科学检查通过 |
| reconstructed feature pass | 2 | T008、T009 的相变特征通过，但两个参数来自后续同作者论文 |
| reconstructed partial | 1 | T010 相结构通过，稳态第二峰权重明显偏弱 |
| failed | 0 | 没有科学断言失败 |
| excluded non-numeric | 3 | 三个能级/装置示意子图 |

## 逐目标

| Target | 论文内容 | 科学状态 | 像素分 | 直接差异 | 根本原因 |
| --- | --- | --- | ---: | --- | --- |
| T001 | Fig. 1(B) SCGF/activity/Mandel | paper-exact pass | 93.6753 | 无关键差异 | — |
| T002 | Fig. 1(C) rate function | paper-exact pass | 94.9667 | 无关键差异 | — |
| T003 | Fig. 1(D) event records | statistical pass | 81.7673 | 单次随机记录不逐像素相同 | 随机实现的自然波动 |
| T004 | Fig. 2(B) three-level SCGF | paper-exact feature pass | 93.9161 | 有限参数下 active branch 相对差 `6.13%` | 论文陈述是渐近关系 |
| T005 | Fig. 2(C) activity/Mandel | paper-exact feature pass | 93.6511 | 无关键差异 | — |
| T006 | Fig. 2(D) rate function | paper-exact feature pass | 95.0582 | 最小值位置误差 `0.00546` | 有限网格 |
| T007 | Fig. 2(E) blinking records | statistical pass | 95.5147 | 事件时间不逐点相同 | 随机实现的自然波动 |
| T008 | Fig. 3(B) micromaser | reconstructed feature pass | 91.2480 | 不能证明曲线权重 paper-exact | 原文缺 `N_ex`、热占据数 |
| T009 | Fig. 3(C) micromaser | reconstructed feature pass | 93.9314 | 不能证明曲线权重 paper-exact | 原文缺 `N_ex`、热占据数 |
| T010 | Fig. 3(D) distributions | reconstructed partial | 96.5188 | 第二峰/主峰仅 `0.007065` | 原文缺参数；另有标签疑点 |
| T011 | Doob mapping | paper-exact pass | N/A | trace residual `6.31e-15` | — |

所有像素比较都发生在数值冻结之后。`outputs/checks/pixel_evidence.json` 是渲染证据，`outputs/checks/science_checks.json` 才记录可证伪的物理量。
