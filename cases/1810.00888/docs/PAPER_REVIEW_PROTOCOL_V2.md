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

本案例已重新完成真正的两阶段 fresh-context 评审。Phase 1 只读取全文与补充
材料，独立冻结 28 项清单：9 个数值图项和 19 个可数字化定量声明；canonical
fingerprint 为 `579b62b5...29e1a836`。Phase 2 后仅通过显式双射规范化 item_id，
原始 kind、source_ref、scientific_basis 和顺序均保持不变；最终 inventory
fingerprint 为 `a30c0a43...369f41f1`。

Phase 2 的 bundle 包含 `implementation/parameter_provenance.json`，但不含旧
评审、案例叙事或会话解释。正式 Harness validator 同时验证两份 bundle 哈希、
Phase 1 清单哈希、28→28 双射、九个目标的证伪记录和候选强证据门，最终
`status=passed`、`gate_errors=0`。裁决为 T001、T002、T006、T007
`paper_error_candidate`，T003–T005、T008–T009 `paper_supported`。

`FORMULA_VERIFICATION.md` 是 Phase 2 读取并哈希冻结的审查前公式门快照，其中
“待独立复核”的措辞用于证明当时没有预写结论；当前裁决只以
`outputs/checks/independent_review.json` 和权威状态文件为准。
