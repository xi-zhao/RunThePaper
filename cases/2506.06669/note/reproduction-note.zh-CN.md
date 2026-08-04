# Remote Entanglement Generation Via Enhanced Quantum State Transfer：科学数值复现说明

## 结论先行

这是 `2506.06669` 的历史科学复现公开包，公开状态为 **Historical scientific artifact (10 numerical targets; 10 figure_rendered)**，冻结审计分为 **68.73/100**。这个分数记录证据强度，不等于论文整体正确率，也不等于复现已经 complete。

本项目的“复现”指理解论文、跟随公式或方法、独立实现数值计算，再生成数据和图。数值数据来自公式、独立数值计算或解析推导，不来自论文图像像素采样。 原论文 PDF、原图、像素提取点、比较板、作者代码与内部运行记录均未公开。已有正式的独立实现证明。

## 数值目标

| Target | 论文图/对象 | 科学含义 | 冻结状态 | 参数匹配 |
| --- | --- | --- | --- | --- |
| `T001` | FIG1CD | Zig-zag spectrum and signed eigenfunction parity structure. | figure_rendered | unknown |
| `T002` | FIG2ABC_S2_S3 | Analytic three-site PST solution space and detuning-time spectra. | figure_rendered | paper_subset |
| `T003` | FIG2DEF | Five-site PST population spectra and even-site suppression. | figure_rendered | paper_subset |
| `T004` | FIG3AB | Master-equation FST dynamics for m=0 and m=4. | figure_rendered | paper_subset |
| `T005` | FIG3CD | Theory density support for remote Bell generation. | figure_rendered | paper_subset |
| `T006` | FIG3E_S8DEF | FST robustness under even-frequency, odd-frequency and coupling noise. | figure_rendered | paper_subset |
| `T007` | FIG4_ACDF | Separable 3x3 FST dynamics and ideal four-corner W density. | figure_rendered | paper_subset |
| `T008` | FIGS7DEF | PST robustness under three independent parameter-noise channels. | figure_rendered | paper_subset |
| `T009` | FIGS9 | One-dimensional Lindblad Bell fidelity versus m and theory density matrices. | figure_rendered | paper_subset |
| `T010` | FIGS10 | Two-dimensional Lindblad W fidelity versus m and population spectra. | figure_rendered | paper_subset |

## 公开内容

- 独立生成数据：10 个文件；
- 独立生成图：11 个文件；
- 可运行代码：`code/`；
- 机器可读边界与评分：`outputs/checks/`。

运行 `python code/scripts/verify_public_artifacts.py` 可以重新计算所有公开文件的哈希、格式与非空检查。数值入口源码也保留在 `code/scripts/` 和 `code/src/`，但部分历史脚本需要论文特定参数或外部公开数据，具体边界以代码注释和数值方法文档为准。

## 尚未解决的边界

冻结状态中仍有未完成、近似或失败的 target：T001=figure_rendered、T002=figure_rendered、T003=figure_rendered、T004=figure_rendered、T005=figure_rendered、T006=figure_rendered、T007=figure_rendered、T008=figure_rendered、T009=figure_rendered、T010=figure_rendered。本公开投影不包含原图比较板、数字化曲线或任何图像导出的坐标。

公开包只保留科学数值结果及其实现。画幅、字体、轴位置、线型和调色板可以用于渲染诊断，但不能改变物理参数、数值数组或用原图像素替代科学计算。
