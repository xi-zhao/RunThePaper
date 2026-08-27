# Strongly correlated quantum walks with a 12-qubit superconducting processor：科学复现讲义

## 结论

Case scaffolded from framework/templates/paper_case.

公开状态为 **Partial scientific reproduction**。这表示公开包忠实保存当前证据边界，并不把 partial、review pending 或 paper-error assessment pending 包装成 complete。

## 我们复现的是什么

本 case 先理解全文和公式，再用独立代码进行数值化。数值 runner 不把论文原图像素、作者数值数组或作者源码作为科学输入；原图只在数值数据冻结后用于画幅与科学区域对比。公开包包含公式推导、独立实现、生成数据、生成图、机器检查和有限的对比板。

当前权威维度：`artifact_integrity=artifact_valid, numerical_scope=complete, parameters=mixed, parameter_provenance=passed, causal_resolution=terminal_blocker, science=pending, execution=attested, pixel=missing, independent_review=missing, review_scope=missing, paper_assessment=missing`。

## 运行

从 `code` 目录执行 `python scripts/run_reproduction.py`，并使用主 README 给出的参数。普通复现入口会调用独立数值实现；算力较大的 paper-scale runner 和配置也保留在 `code/scripts` 与 `code/config`，但没有实际完成的计算绝不会被标记为已运行。

## 论文审查边界

如果公式、图注或结论与独立计算稳定冲突，公开文档会记录该差异；只有证伪流程和独立评审满足后才升级为论文错误候选。当前限制：Published article and 35-page supplementary material ingested from institutional mirrors and recorded by SHA-256. The full paper and supplement contain 38 independently computable theoretical numerical items; all 38 have atomic targets and generated data. Experimental hardware measurements and raw tomography are excluded from the numerical-runner denominator. The current isolated CPU run attests all 38 targets; the historical A100 result is backend-portability evidence only. Twelve S20 panels retain an unresolved printed-time/source discrepancy, and S11 lacks author realization-level parameters.
