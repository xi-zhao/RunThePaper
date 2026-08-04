# Emergent photons and mechanisms of confinement：科学数值复现说明

## 结论先行

这是 `2505.00079` 的历史科学复现公开包，公开状态为 **Historical scientific artifact (8 numerical targets; 3 blocked_compute_scale, 1 failed, 4 partially_reproduced)**，冻结审计分为 **30.20/100**。这个分数记录证据强度，不等于论文整体正确率，也不等于复现已经 complete。

本项目的“复现”指理解论文、跟随公式或方法、独立实现数值计算，再生成数据和图。数值数据来自公式、独立数值计算或解析推导，不来自论文图像像素采样。 原论文 PDF、原图、像素提取点、比较板、作者代码与内部运行记录均未公开。这是历史案例，尚未补齐机器可验证的作者代码隔离证明，因此公开状态不会被自动升级为 complete。

## 数值目标

| Target | 论文图/对象 | 科学含义 | 冻结状态 | 参数匹配 |
| --- | --- | --- | --- | --- |
| `T001` | FIG002 | Z7 Polyakov order parameter and defect ordering across beta. | partially_reproduced | reduced_scale |
| `T002` | FIG002 | Polyakov phase distributions and representative defects. | partially_reproduced | reduced_scale |
| `T003` | FIG003 | Circular Z4 Polyakov histogram in the photon phase. | partially_reproduced | paper_subset |
| `T004` | FIG004 | Two Z3 susceptibility peaks and Polyakov distributions. | failed | reduced_scale |
| `T005` | FIG005 | Z3/Z4/Z7 correlator ratios approaching the Coulomb curve. | partially_reproduced | paper_subset |
| `T006` | SMFIG001 | Binned error saturation justifying 500 skipped sweeps. | blocked_compute_scale | not_applicable |
| `T007` | SMFIG002 | Raw plaquette correlator components. | blocked_compute_scale | not_applicable |
| `T008` | SMTAB002 | Power-series coefficients of total correlators. | blocked_compute_scale | not_applicable |

## 公开内容

- 独立生成数据：5 个文件；
- 独立生成图：1 个文件；
- 可运行代码：`code/`；
- 机器可读边界与评分：`outputs/checks/`。

运行 `python code/scripts/verify_public_artifacts.py` 可以重新计算所有公开文件的哈希、格式与非空检查。数值入口源码也保留在 `code/scripts/` 和 `code/src/`，但部分历史脚本需要论文特定参数或外部公开数据，具体边界以代码注释和数值方法文档为准。

## 尚未解决的边界

冻结状态中仍有未完成、近似或失败的 target：T001=partially_reproduced、T002=partially_reproduced、T003=partially_reproduced、T004=failed、T005=partially_reproduced、T006=blocked_compute_scale、T007=blocked_compute_scale、T008=blocked_compute_scale。该历史案例尚无机器可验证的作者代码隔离证明。本公开投影不包含原图比较板、数字化曲线或任何图像导出的坐标。

公开包只保留科学数值结果及其实现。画幅、字体、轴位置、线型和调色板可以用于渲染诊断，但不能改变物理参数、数值数组或用原图像素替代科学计算。
