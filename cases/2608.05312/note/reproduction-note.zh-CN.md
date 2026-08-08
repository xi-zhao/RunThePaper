# arXiv:2608.05312 独立复现笔记

## 论文与问题

本文复现 [Unidirectional Dark-to-Bright Rescue in Cavity-Coupled Quantum
Transport](https://arxiv.org/abs/2608.05312) 的开放量子系统数值结果。论文研究
一个无序发射体链与单模腔耦合后的输运：大部分激发会进入几乎不含光子成分
的暗态，普通退相干只能双向混合明暗流形，而非 Condon 弛豫通道可以把暗态
单向送回明态，再由腔损耗排入 sink。

公开包从 Lindblad 方程独立计算结果，不读取作者数值数据。它覆盖论文中
所有公开信息足以执行的十个数值目标：主文 Fig. 1(c)、Fig. 2、Fig. 3，
补充 Fig. S1–S4，以及 Table S1、Table S2。

## 核心模型

单激发基底为 `[cavity, site 1, ..., site N, sink]`。代码分别构造：

- Tavis–Cummings–Hubbard 相干 Hamiltonian；
- 发射体到腔的 rescue 跳跃与反向热吸收；
- 各 site 的纯退相干；
- 腔 drain 或末端 site drain；
- 明态、暗态、腔和 sink 的投影观测量。

密度矩阵使用列向量化的稀疏 Liouvillian，通过
`scipy.sparse.linalg.expm_multiply` 演化。小系统与稠密矩阵指数的最大差异为
`3.40e-16`，迹、Hermiticity 和正定性检查均通过。完整公式见
[DERIVATION.md](../docs/DERIVATION.md)。

## 复现结果

十个可执行目标全部通过，综合证据评分为 **83.4/100**，物理特征匹配为
**99.7%**。这是数值特征复现，不是作者原始数据的逐点复制。

- 尺度律拟合得到斜率 `0.2871`，论文值为 `0.29`；幂律指数为 `0.799`，
  论文值为 `0.77`。
- cavity drain 下，rescue 在 `N=3..96` 的最优输运效率均高于 `0.998`；
  dephasing 随系统增大而明显退化。
- `N=6` 动力学中，rescue 的明态峰值为 `0.586`；dephasing 终点暗态占据为
  `0.159`，sink 效率为 `0.796`。
- 温度边界在 `N=6` 时由 `0.0845` 移到 `0.1629`，对应论文约
  `0.08 -> 0.16`；`N=64` 时得到 `0.00756 -> 0.01497`，对应论文约
  `0.008 -> 0.015`。
- Table S1 的七种机制排序全部一致，MAE 为 `0.00615`；Table S2 的失谐
  数据 MAE 为 `0.00182`。
- drain 改到末端 site 后，机制排序反转，dephasing 优于 rescue，与补充材料
  一致。

生成图、CSV 数据和机器检查分别位于 `outputs/figures/`、`outputs/data/`
和 `outputs/checks/`。有限的论文摘录对照板位于
[docs/comparisons](../docs/comparisons/)，只用于核对结构和关键特征，不代表
作者数据级等价。

## 快速运行

从本案例的 `code/` 目录运行：

```bash
python scripts/run_checks.py
python scripts/run_reproduction.py \
  --profile quick \
  --targets all \
  --output-root ../outputs/quick
```

论文参数子集运行：

```bash
python scripts/run_reproduction.py \
  --profile paper_subset \
  --targets all \
  --output-root ../outputs/paper_subset
```

快速配置用于验证完整流程；正式提交结果使用 `paper_subset` 配置。后者在
16 GiB Apple M4 上约需十余分钟，主要时间花在 `N=96` 尺度扫描和
`N=64` 温度图。

## 复现边界

论文没有给出平均 hopping `t`、精确初态记号、作者随机种子和完整扫描网格。
本复现通过 Table S2、温度边界、尺度律和论文给出的峰位共同约束
`t=1 meV`，但仍将所有结果标记为 `paper_subset / exploratory`。

补充 Fig. S4 的 `N=64` 温度图使用 5 个 disorder realizations 和 `9x9`
网格，物理边界已复现，但统计精度低于论文声明的 15 realizations。
Fig. S5 的 QCLE 计算没有复现，因为论文没有公开 lead/bath 矩阵、化学势、
初态和可运行实现；增加计算资源无法补回这些输入。

公开仓库不包含论文 PDF、arXiv 源码包、独立原图或提取曲线。所有公开数据
和右侧复现图均由本案例代码生成。
