# Exact Fractionalized Ground States in an Extended Spin-1 Kitaev Chain：科学复现讲义

## 结论

The two Main Fig. 5 panels and two central periodic analytic families are independently covered, while a full-paper audit exposes five supplemental claim families without accepted implementations. The legacy two-panel similarity score remains 95; whole-paper coverage and reproduction degree are derived separately.

公开状态为 **Partial scientific reproduction**。这表示公开包忠实保存当前证据边界，并不把 partial、review pending 或 paper-error assessment pending 包装成 complete。

## 我们复现的是什么

本 case 先理解全文和公式，再用独立代码进行数值化。数值 runner 不把论文原图像素、作者数值数组或作者源码作为科学输入；原图只在数值数据冻结后用于画幅与科学区域对比。公开包包含公式推导、独立实现、生成数据、生成图、机器检查和有限的对比板。

当前权威维度：`artifact_integrity=artifact_valid_with_warnings, numerical_scope=complete, parameters=mixed, parameter_provenance=passed, causal_resolution=repair_required, science=failed, execution=attested, pixel=missing, independent_review=passed, review_scope=complete, paper_assessment=inconclusive`。

## 运行

从 `code` 目录执行 `python scripts/run_reproduction.py`，并使用主 README 给出的参数。普通复现入口会调用独立数值实现；算力较大的 paper-scale runner 和配置也保留在 `code/scripts` 与 `code/config`，但没有实际完成的计算绝不会被标记为已运行。

## 论文审查边界

如果公式、图注或结论与独立计算稳定冲突，公开文档会记录该差异；只有证伪流程和独立评审满足后才升级为论文错误候选。当前限制：All 25 first-excited values agree with the digitized source within 0.0015. The ground-state panel has one retained 0.00364 discrepancy at theta=10 degrees, N=12; the remaining 24 values agree within 0.0015. The paper omits eigensolver and tolerance details, so the two rendered overlap artifacts remain exploratory despite their strong numerical agreement. The full-paper item audit finds 9 eligible scientific items: 4 covered and 5 uncovered, for 44.44% coverage and reproduction degree 40.90. V003-V007 expose three open-chain results, one parity-selection rule, and one perturbative-sector claim that still lack independent implementations.
