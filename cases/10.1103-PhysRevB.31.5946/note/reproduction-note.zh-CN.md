# Phase diagrams and critical behavior of Ising square lattices with nearest-, next-nearest-, and third-nearest-neighbor couplings：科学数值复现说明

## 结论先行

这是 `10.1103-PhysRevB.31.5946` 的历史科学复现公开包，公开状态为 **Historical scientific artifact (15 numerical targets; 11 blocked_missing_method, 1 blocked_missing_parameter, 2 failed, 1 reproduced)**，冻结审计分为 **11.20/100**。这个分数记录证据强度，不等于论文整体正确率，也不等于复现已经 complete。

本项目的“复现”指理解论文、跟随公式或方法、独立实现数值计算，再生成数据和图。数值数据来自公式、独立数值计算或解析推导，不来自论文图像像素采样。 原论文 PDF、原图、像素提取点、比较板、作者代码与内部运行记录均未公开。这是历史案例，尚未补齐机器可验证的作者代码隔离证明，因此公开状态不会被自动升级为 complete。

## 数值目标

| Target | 论文图/对象 | 科学含义 | 冻结状态 | 参数匹配 |
| --- | --- | --- | --- | --- |
| `T002` | FIG002 | Exact zero-temperature phase diagram. | reproduced | paper_exact |
| `T004` | FIG004 | Free-energy and entropy integration. | blocked_missing_method | not_applicable |
| `T005` | FIG005 | R=1 and 1.5 phase boundaries. | blocked_missing_method | not_applicable |
| `T006` | FIG006 | R=0.25, 0.5, and 0.75 phase boundaries. | blocked_missing_method | not_applicable |
| `T007` | FIG007 | R=-1, -0.5, and 0 phase boundaries. | blocked_missing_method | not_applicable |
| `T008` | FIG008 | Three-dimensional phase diagram. | blocked_missing_method | not_applicable |
| `T009` | FIG009 | Specific heat for R=0, R'=0.8. | failed | paper_subset |
| `T010` | FIG010 | First-order peak finite-size scaling. | failed | paper_subset |
| `T011` | FIG011 | Binder cumulant crossings. | blocked_missing_method | not_applicable |
| `T012` | FIG012 | Cumulant-derived critical parameters. | blocked_missing_method | not_applicable |
| `T013` | FIG013 | Critical temperature and exponent versus R. | blocked_missing_method | not_applicable |
| `T014` | FIG014 | Fixed-point cumulant versus R. | blocked_missing_method | not_applicable |
| `T015` | FIG015 | Bulk finite-size scaling with source R conflict. | blocked_missing_parameter | not_applicable |
| `T016` | FIG016 | First-order discontinuities. | blocked_missing_method | not_applicable |
| `T017` | FIG017 | Temperature-dependent order parameters. | blocked_missing_method | not_applicable |

## 公开内容

- 独立生成数据：2 个文件；
- 独立生成图：2 个文件；
- 可运行代码：`code/`；
- 机器可读边界与评分：`outputs/checks/`。

运行 `python code/scripts/verify_public_artifacts.py` 可以重新计算所有公开文件的哈希、格式与非空检查。数值入口源码也保留在 `code/scripts/` 和 `code/src/`，但部分历史脚本需要论文特定参数或外部公开数据，具体边界以代码注释和数值方法文档为准。

## 尚未解决的边界

冻结状态中仍有未完成、近似或失败的 target：T004=blocked_missing_method、T005=blocked_missing_method、T006=blocked_missing_method、T007=blocked_missing_method、T008=blocked_missing_method、T009=failed、T010=failed、T011=blocked_missing_method、T012=blocked_missing_method、T013=blocked_missing_method、T014=blocked_missing_method、T015=blocked_missing_parameter、T016=blocked_missing_method、T017=blocked_missing_method。该历史案例尚无机器可验证的作者代码隔离证明。本公开投影不包含原图比较板、数字化曲线或任何图像导出的坐标。

公开包只保留科学数值结果及其实现。画幅、字体、轴位置、线型和调色板可以用于渲染诊断，但不能改变物理参数、数值数组或用原图像素替代科学计算。
