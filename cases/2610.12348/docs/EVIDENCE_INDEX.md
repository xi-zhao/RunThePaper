# 证据索引 / Evidence map

| 报告结论 | 实现或定义 | 生成数据／检查 |
|---|---|---|
| 暗态、配对量子数、相关 | [静态算法](../code/h3/solvers/generate_statics.py)、[推导](DERIVATION.md) | [静态结果](../outputs/data/statics.json)、[静态数组](../outputs/data/statics.npz)、[代数检查](../outputs/data/algebra-conserved.json) |
| 主动力学 | [轨迹](../code/h3/solvers/generate_dynamics.py) | [动力学](../outputs/data/dynamics.json)、[数组](../outputs/data/dynamics.npz) |
| 相干 GS 与 cutoff | [相干求解器](../code/h3/solvers/generate_coherent_packed.py) | [GS](../outputs/data/coherent-gs.npz)、[64 条配对](../outputs/data/coherent-cutoff-64-controls.json) |
| H1 观测量 | [原始生成数据](../outputs/data/h1-weighted-control.npz) | [参数与均值](../outputs/data/h1-weighted-control.json)、[聚合比较](../outputs/checks/statistical-summary.json) |
| H2 分箱及尾部 | [分箱推导程序](../code/base/scripts/derive_h2_bins_v1.py)、[尾部程序](../code/base/scripts/generate_h2_tail_v2.py) | [有界尾部检查](../outputs/checks/h2-tail.json)、[聚合统计](../outputs/checks/statistical-summary.json) |
| H3 归一化诊断 | [生成器](../code/h3/generate.py)、[配置](../code/h3/config.json) | [逐轨迹数组](../outputs/data/h3/samples.npz)、[结果](../outputs/data/h3/results.json)、[聚合残差](../outputs/checks/h3-summary.json) |
| 全文判断与公开边界 | [量化口径](QUANTIFICATION.md)、[差异清单](BOUNDARIES.md) | [逐项投影](../outputs/checks/completion_assessment.json)、[来源散列](../outputs/checks/publication_provenance.json) |

这些生成数组是我们的结果，不是作者原始数据。图像对照、逐对象判断、运行成功和整个目标完成是不同证据。原图读点不作为公开数据集分发；复算主科学程序不需要它们。
