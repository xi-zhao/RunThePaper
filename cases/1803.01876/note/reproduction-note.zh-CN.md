# Edge states and topological invariants of non-Hermitian systems：科学复现讲义

## 结论

所有评分 target 已加入原文图源 digitization：Fig. 2、Fig. 3、Fig. 4、Fig. 5 和补充图均有 EPS/PNG reference CSV 与 generated data 对照。Fig. 2/Fig. 3 共用的开链实空间方程和补充图使用的开边界 bulk spectrum 均已升级为 source_and_symbolic 公式门禁；剩余边界是：这些仍不是作者原始 plotting data。

公开状态为 **Partial scientific reproduction**。这表示公开包忠实保存当前证据边界，并不把 partial、review pending 或 paper-error assessment pending 包装成 complete。

## 我们复现的是什么

本 case 先理解全文和公式，再用独立代码进行数值化。数值 runner 不把论文原图像素、作者数值数组或作者源码作为科学输入；原图只在数值数据冻结后用于画幅与科学区域对比。公开包包含公式推导、独立实现、生成数据、生成图、机器检查和有限的对比板。

当前权威维度：`artifact_integrity=artifact_valid, numerical_scope=complete, parameters=mixed, parameter_provenance=passed, causal_resolution=repair_required, science=failed, execution=attested, pixel=missing, independent_review=passed, review_scope=complete, paper_assessment=inconclusive`。

## 运行

从 `code` 目录执行 `python scripts/run_reproduction.py`，并使用主 README 给出的参数。普通复现入口会调用独立数值实现；算力较大的 paper-scale runner 和配置也保留在 `code/scripts` 与 `code/config`，但没有实际完成的计算绝不会被标记为已运行。

## 论文审查边界

如果公式、图注或结论与独立计算稳定冲突，公开文档会记录该差异；只有证伪流程和独立评审满足后才升级为论文错误候选。当前限制：Remaining lifecycle boundaries: parameters=mixed, causal_resolution=repair_required, science=failed, pixel=missing, paper_assessment=inconclusive.
