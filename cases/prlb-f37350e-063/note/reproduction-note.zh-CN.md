# 非互易驱动耗散凝聚态相变：公式驱动的数值复现

## 结论

本 case 从论文方程独立构造非互易晶格模型，覆盖主文 Fig. 1–6 以及补充材料
Fig. S1、S2(a)、S3 的主要数值内容。当前属于**部分全文数值复现**，不是完整复现：
12 个已执行 target 的科学检查全部通过，但仍有 4 个高成本数值项没有闭合。

综合复现分为 **76.75/100**；预声明科学区域的平均灰度像素相似度为
**86.56/100**，平均 SSIM 为 **0.5330**。像素指标只评价独立数值结果是否被忠实
绘制，不能替代公式、参数和动力学检查。

## 我们复现了什么

- Eq. (1) 的 PBC/OBC 复谱与真空阈值；
- Eq. (2) 的非线性开放边界动力学、静态 kink 和相结构；
- PBC 行波的存在区及 Bogoliubov 稳定性；
- Lyapunov 指数、相空间轨迹与粒子-空穴对称性；
- 补充材料中的临界例外点曲线、混沌空间畴和边缘动力学。

几个定量结果：静态 kink 指数为 `-0.5045`（论文 `-0.5`）；动态频率与解析
色散的 RMSE 为 `0.00625`；独立得到的粒子-空穴周期为 `26.655`（论文
`26.66`）。

## 独立检查发现的问题

1. 补充材料给出的 2×2 稳定性矩阵要求本征值根式中出现 `4 Lambda^2`；印刷闭式
   只有 `Lambda^2`。修正后与直接对角化的最大误差为 `2.7e-15`。
2. Fig. S1 图注中 `gamma=0.1` 和 `0.2` 的临界 kappa，与独立 Jacobian 零点分别
   相差约 `0.00671` 和 `0.00540`；`gamma=0.3` 在 `4e-5` 内一致。

## 科学边界

数值程序不读取论文图片、提取曲线、作者数值代码或作者数值数据。论文图只在数值
数组生成并冻结之后进入单独的排版比较，用于画幅、字体、配色和科学区域像素诊断；
它不能改变物理参数或数值数组。公开比较板中的论文小片段仅用于核查结构，不代表
作者数据级别的一致。

## 运行

从本 case 的 `code` 目录快速重绘全部公开图：

```bash
python scripts/render_fast_formula_targets.py
python scripts/render_dynamic_targets.py
python scripts/render_cep_targets.py
python scripts/render_phase_diagram_targets.py
```

完整重新计算当前已实现 target：

```bash
python scripts/run_fast_formula_targets.py
python scripts/run_dynamic_targets.py
python scripts/run_cep_targets.py
python scripts/run_phase_diagram_targets.py
```

本地完整计算约需数分钟，动态阶段峰值内存约 2.2 GiB。运行结果写入
`../outputs/data`、`../outputs/checks` 和 `../outputs/figures`。

## 尚未闭合

- Main Fig. 3(a) 的论文分辨率相边界；
- Main Fig. 4(a) 的精细多稳态条纹；
- Main Fig. 4(d) 的完整五吸引子层级；
- Supplemental Fig. S2(b) 的 300 条邻近轨迹。

因此这个公开 case 应被理解为可运行、可审计、边界明确的科学数值复现，而不是对
整篇论文全部图形和作者数据的替代。
