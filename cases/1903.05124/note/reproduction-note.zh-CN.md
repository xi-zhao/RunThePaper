# Quantum Error Correction in Scrambling Dynamics and Measurement-Induced Phase Transition：科学复现讲义

## 结论

Full twenty-page arXiv PDF and both TeX manuscripts read before target selection.

公开状态为 **Partial scientific reproduction**。这表示公开包忠实保存当前证据边界，并不把 partial、review pending 或 paper-error assessment pending 包装成 complete。

## 我们复现的是什么

本 case 先理解全文和公式，再用独立代码进行数值化。数值 runner 不把论文原图像素、作者数值数组或作者源码作为科学输入；原图只在数值数据冻结后用于画幅与科学区域对比。公开包包含公式推导、独立实现、生成数据、生成图、机器检查和有限的对比板。

当前权威维度：`artifact_integrity=artifact_valid_with_warnings, numerical_scope=complete, parameters=mixed, parameter_provenance=missing, causal_resolution=repair_required, science=passed, execution=attested, pixel=needs_repair, independent_review=missing, review_scope=missing, paper_assessment=missing`。

## 运行

从 `code` 目录执行 `python scripts/run_reproduction.py`，并使用主 README 给出的参数。普通复现入口会调用独立数值实现；算力较大的 paper-scale runner 和配置也保留在 `code/scripts` 与 `code/config`，但没有实际完成的计算绝不会被标记为已运行。

## 论文审查边界

如果公式、图注或结论与独立计算稳定冲突，公开文档会记录该差异；只有证伪流程和独立评审满足后才升级为论文错误候选。当前限制：All 44 visible theory-numerical panels and insets are frozen in the reproduction scope. Nine schematic panels and one numerical summary table are inventoried but excluded from figure generation. Source figures are comparison-only; every generated value must come from formulas or an independent Clifford/stabilizer computation. T001 now has a feature-scale reproduction of all four Main Fig. 2 numerical panels; paper geometry is preserved while sampling and finite-size grids remain reduced and explicitly labeled. T004 now has all ten Supplement Fig. S4 numerical items from a fresh EQC007 half-chain fit over independent generated observations; every scientific check passes at feature scale. T005 now has all seven Supplement Fig. S5 panels from 4,352 independent periodic-chain trajectories; critical points pass, while exponent-depth stability remains partial at L<=24 and eight realizations per cell. T006 now has all three Supplement Fig. S6 panels from 2,880 independent trajectories over every paper block size at exact d/m=3; all frozen scientific checks pass at feature scale, with sizes limited to L<=24. All 44 theory-numerical items now have independent formula-based evidence; 20 are paper scale and 24 are explicitly feature scale.
