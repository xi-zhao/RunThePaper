# Enhancing Revivals via Projective Measurements in a Quantum Scarred System：科学数值复现说明

## 结论先行

这是 `2503.22618` 的历史科学复现公开包，公开状态为 **Historical scientific artifact (8 numerical targets; 7 blocked_missing_method, 1 reproduced)**，冻结审计分为 **0.00/100**。这个分数记录证据强度，不等于论文整体正确率，也不等于复现已经 complete。

本项目的“复现”指理解论文、跟随公式或方法、独立实现数值计算，再生成数据和图。数值数据来自公式、独立数值计算或解析推导，不来自论文图像像素采样。 原论文 PDF、原图、像素提取点、比较板、作者代码与内部运行记录均未公开。这是历史案例，尚未补齐机器可验证的作者代码隔离证明，因此公开状态不会被自动升级为 complete。

## 数值目标

| Target | 论文图/对象 | 科学含义 | 冻结状态 | 参数匹配 |
| --- | --- | --- | --- | --- |
| `T_FIG1` | FIG_MAIN_1 | Random-monitoring entanglement dynamics. | blocked_missing_method | not_applicable |
| `T_FIG2` | FIG_MAIN_2 | Periodic-monitoring fidelity and entanglement. | blocked_missing_method | not_applicable |
| `T_FIG3` | FIG_MAIN_3 | Post-measurement scar weight versus time. | blocked_missing_method | not_applicable |
| `T_FIG4` | FIG_MAIN_4 | Scar phase and amplitude resynchronization. | blocked_missing_method | not_applicable |
| `T_FIGS1` | FIG_SUPP_1 | Entanglement-velocity change after measurement. | blocked_missing_method | not_applicable |
| `T_FIGS2` | FIG_SUPP_2 | Long-time entropy-density finite-size curves. | blocked_missing_method | not_applicable |
| `T_FIGS3` | FIG_SUPP_3 | Bayesian finite-size data collapse. | blocked_missing_method | not_applicable |
| `T_BENCH` | BENCH_EXT | Exact audit of the synthetic Bayesian scar-weight LDP extension. | reproduced | not_applicable |

## 公开内容

- 独立生成数据：1 个文件；
- 独立生成图：1 个文件；
- 可运行代码：`code/`；
- 机器可读边界与评分：`outputs/checks/`。

运行 `python code/scripts/verify_public_artifacts.py` 可以重新计算所有公开文件的哈希、格式与非空检查。数值入口源码也保留在 `code/scripts/` 和 `code/src/`，但部分历史脚本需要论文特定参数或外部公开数据，具体边界以代码注释和数值方法文档为准。

## 尚未解决的边界

冻结状态中仍有未完成、近似或失败的 target：T_FIG1=blocked_missing_method、T_FIG2=blocked_missing_method、T_FIG3=blocked_missing_method、T_FIG4=blocked_missing_method、T_FIGS1=blocked_missing_method、T_FIGS2=blocked_missing_method、T_FIGS3=blocked_missing_method。该历史案例尚无机器可验证的作者代码隔离证明。本公开投影不包含原图比较板、数字化曲线或任何图像导出的坐标。

公开包只保留科学数值结果及其实现。画幅、字体、轴位置、线型和调色板可以用于渲染诊断，但不能改变物理参数、数值数组或用原图像素替代科学计算。
