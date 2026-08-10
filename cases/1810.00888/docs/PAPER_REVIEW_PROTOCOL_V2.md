# Paper review protocol v2

论文审查与图像复现并列为正式产品能力。任何异常先分为 reproduction_defect、parameter_ambiguity、insufficient_compute 或 paper_error_candidate。

只有同时满足以下条件才允许 paper_error_candidate：

1. 目标采用 paper-exact 参数或解析极限；
2. 收敛性、精确性或闭式推导已经建立；
3. 至少两条真正独立的强交叉检查；
4. 明确指出论文页、公式、图注或源码位置；
5. 已主动证伪替代解释，包括实现错误、简并基、舍入和算力不足；
6. fresh-context 评审者先只看全文完成图表清单，再看公式、代码和生成数据；
7. 评审结果通过机器合同。

本案例曾完成真正的两阶段 fresh-context 评审。Phase 1 原始九项清单以
96a13927...4f9e 冻结；Phase 2 后仅通过显式双射规范化 item_id，原始
kind、source_ref、scientific_basis 和顺序均保持不变。Harness 会同时验证
原始清单哈希、最终清单哈希和一对一映射，任何科学内容变化都会 fail closed。

该历史评审发生在参数来源门落地之前，falsification bundle 不含
`implementation/parameter_provenance.json`。现在参数来源合同及新 bundle 已
生成，旧 submission 的 bundle 指纹不再匹配，机器状态为 `stale`。历史裁决
T001、T002、T006、T007 为 paper_error_candidate，T003–T005、T008–T009 为
paper_supported；这些裁决当前均不具备权威效力。新 reviewer 必须重新完成
两阶段流程，不能复制旧 submission 或读取本案例叙事报告。
