# Demonstrating quantum error mitigation on logical qubits：科学数值复现说明

## 结论先行

这是 `10.1038-s41467-025-67768-4` 的历史科学复现公开包，公开状态为 **Historical scientific artifact (9 numerical targets; 2 blocked_missing_method, 1 failed, 5 partially_reproduced, 1 reproduced)**，冻结审计分为 **72.25/100**。这个分数记录证据强度，不等于论文整体正确率，也不等于复现已经 complete。

本项目的“复现”指理解论文、跟随公式或方法、独立实现数值计算，再生成数据和图。数值数据来自公式、独立数值计算或解析推导，不来自论文图像像素采样。 原论文 PDF、原图、像素提取点、比较板、作者代码与内部运行记录均未公开。这是历史案例，尚未补齐机器可验证的作者代码隔离证明，因此公开状态不会被自动升级为 complete。

## 数值目标

| Target | 论文图/对象 | 科学含义 | 冻结状态 | 参数匹配 |
| --- | --- | --- | --- | --- |
| `T001` | MAIN_FIG2C | Feedback/post-selection expectation under amplified Pauli injection. | failed | paper_subset |
| `T002` | MAIN_FIG3C | One-round corrected and uncorrected repetition-code expectations. | partially_reproduced | paper_subset |
| `T003` | MAIN_FIG3E | Multi-round distance-7 repetition-code expectation at approximately fixed total error. | partially_reproduced | paper_subset |
| `T004` | MAIN_FIG4BC | Distance-3 surface-code logical Pauli channel, Bloch-circle contraction, and state-specific logical observables. | partially_reproduced | paper_subset |
| `T005` | SUPP_FIG8 | Complete versus injection-only ZNE bias and sampling overhead. | partially_reproduced | paper_subset |
| `T006` | SUPP_FIG9 | Large-scale surface-code logical-memory ZNE bias and overhead. | reproduced | paper_exact |
| `T007` | SUPP_TABLE3 | Per-layer unit-error probabilities intended to preserve cumulative injected error. | partially_reproduced | paper_exact |
| `T008` | SUPP_FIG2 | [[72,12,6]] qLDPC Monte Carlo logical-error distribution. | blocked_missing_method | unknown |
| `T009` | SUPP_FIG10BC | Lattice-surgery circuit-level Monte Carlo ZNE bias and overhead. | blocked_missing_method | unknown |

## 公开内容

- 独立生成数据：7 个文件；
- 独立生成图：10 个文件；
- 可运行代码：`code/`；
- 机器可读边界与评分：`outputs/checks/`。

运行 `python code/scripts/verify_public_artifacts.py` 可以重新计算所有公开文件的哈希、格式与非空检查。数值入口源码也保留在 `code/scripts/` 和 `code/src/`，但部分历史脚本需要论文特定参数或外部公开数据，具体边界以代码注释和数值方法文档为准。

## 尚未解决的边界

冻结状态中仍有未完成、近似或失败的 target：T001=failed、T002=partially_reproduced、T003=partially_reproduced、T004=partially_reproduced、T005=partially_reproduced、T007=partially_reproduced、T008=blocked_missing_method、T009=blocked_missing_method。本公开投影不包含原图比较板、数字化曲线或任何图像导出的坐标。

公开包只保留科学数值结果及其实现。画幅、字体、轴位置、线型和调色板可以用于渲染诊断，但不能改变物理参数、数值数组或用原图像素替代科学计算。
