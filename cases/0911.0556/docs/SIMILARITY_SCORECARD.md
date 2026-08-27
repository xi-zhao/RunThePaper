# Similarity Scorecard

## 评分结果

- Unified reproduction degree：`77.78/100`。
- Current level：`partial_reproduction`；uncapped scientific level 为 `scientific_feature_reproduction`。
- 10 个科学区域原始像素分均值：`93.0248`。
- Item coverage：`27/27 = 100%`；covered-item mean fidelity：`77.78`。
- Evidence grade：`E2`（12 个目标均已有当前隔离运行凭证；fresh independent review 尚未更新）。

像素差是有图目标的主比较量；科学证据门负责封顶。T008–T010 即使像素分高，也因原论文参数缺失被限制在 `50`，防止用渲染相似掩盖参数身份不明。

| Target | Primary pixel/analytic score | Final capped score | 封顶原因 |
| --- | ---: | ---: | --- |
| T001 | 93.6753 | 90 | analytic reference policy |
| T002 | 94.9667 | 90 | analytic reference policy |
| T003 | 81.7673 | 80 | visual feature contract |
| T004 | 93.9161 | 90 | analytic reference policy |
| T005 | 93.6511 | 90 | analytic reference policy |
| T006 | 95.0582 | 90 | analytic reference policy |
| T007 | 95.5147 | 80 | stochastic visual feature contract |
| T008 | 91.2480 | 50 | original parameters unavailable |
| T009 | 93.9314 | 50 | original parameters unavailable |
| T010 | 96.5188 | 50 | original parameters unavailable；feature partial |
| T011 | analytic 90 | 90 | analytic reference policy |
| T012 | analytic 90 | 90 | 显式算符/超算符交叉检查；fresh review pending |

机器记录：`outputs/checks/similarity_scorecard.json`。该文件由 `scripts/build_scorecard.py` 从冻结像素证据与科学检查生成，再由 Harness schema-v4 归一化。

覆盖度与 fidelity 分开：`T012` 补齐后 coverage 达到 100%；T008–T010 虽有完整
代码和数据、所以属于 covered，却因原 Letter 缺参数而在 fidelity 上封顶。这样
可以区分“有没有做”与“证据/论文参数能支持到多精确”。
