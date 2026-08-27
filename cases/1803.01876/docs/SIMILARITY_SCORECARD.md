# 相似度评分卡：1803.01876

## 总分

- Overall score: `94.0/100`
- Similarity level: `complete_reproduction`
- Whole-paper reproduction degree: `82.08/100`
- Item coverage: `22/25 = 88.00%`
- Covered-item fidelity: `93.28`
- Evidence grade: `E1`
- 解释：所有评分 target 已加入原文图源 digitization：Fig. 2、Fig. 3、Fig. 4、Fig. 5 和补充图均有 EPS/PNG reference CSV 与 generated data 对照。Fig. 2/Fig. 3 共用的开链实空间方程和补充图使用的开边界 bulk spectrum 均已升级为 `source_and_symbolic` 公式门禁；剩余边界是：这些仍不是作者原始 plotting data。

`94.0` 是历史五个已实现 target 的 fidelity aggregate；`82.08` 才是本轮统一
全文口径，因为 3 个遗漏 claim 以零分进入 reproduction-degree 分母。T006-T008
在历史 aggregate 中权重为零，避免 inventory 迁移悄悄改写旧分数，但它们会在
coverage 和公开 uncovered 清单中逐项出现。

## 单图评分

| 数值图/表/面板 | Weight | 数值特征吻合度 | 关键数值接近度 | 原文目标覆盖度 | Score | Reference |
| --- | ---: | --- | --- | --- | ---: | --- |
| Fig. 2 open-boundary spectrum | 1.0 | 50/50 - 零能边界态、开边界谱和手征配对都出现，和论文主张一致。 | 34/35 - 从原始图源 digitize Fig. 2(a-c,d) 曲线/点云后，4 个 panel 目标级 mismatch count 为 0；中位最近邻误差均在各自容差内，p95 残余作为版式/分支密度差异保留。 | 13/15 - Fig. 2(a-c,d) 均已有 EPS/PNG digitized reference CSV，并接入 all_digitized_curves.json；仍低于作者原始 plotting data。 | 95 | digitized_curve |
| Fig. 3 GBZ and skin localization | 1.0 | 49/50 - 广义布里渊区和 skin localization 的关键特征出现。 | 33/35 - Fig. 3(a-c) 已加入 raster/EPS digitized reference：beta-root 面板、C_beta 曲线和 profile 面板目标级 mismatch count 为 0。 | 13/15 - Fig. 3 三个 panel 均有 digitized reference CSV；仍不是作者原始 plotting data。 | 95 | digitized_curve |
| Fig. 4 non-Bloch winding number | 1.0 | 50/50 - non-Bloch winding number 平台和拓扑区间清楚出现。 | 34/35 - 从原始 EPS 矢量图提取的 23 个 marker 全部匹配 generated winding，阶跃转变点最大 t1 误差为 0.0082。 | 12/15 - Fig. 4 的原文 marker 和阶跃曲线已从 EPS digitize，并和 generated CSV 建立点级对照；仍低于作者原始数据级别。 | 95 | digitized_curve |
| Fig. 5 nonzero t3 topology | 1.0 | 47/50 - 非零 t3 情况下的拓扑区间和非圆形 C_beta 特征出现。 | 33/35 - Fig. 5(a,b) 的 spectrum、winding 和 C_beta 均由独立物理计算生成；3 个 panel 的 digitized reference mismatch count 为 0。spectrum 可见线按 open-chain `|E|` 能级在 `t1` 上连接，source EPS 只作为 reference comparator。 | 13/15 - 非零 t3 目标的两个主图 panel 均有 digitized reference CSV；仍不是作者原始 plotting data。 | 93 | digitized_curve |
| Supplemental spectra | 0.5 | 45/50 - 补充材料里的复谱和大 gamma 绕数特征出现。 | 32/35 - 补充 Fig. 1 复平面谱、补充 Fig. 2 spectrum 和 winding 已加入 digitized reference；4 个 panel 目标级 mismatch count 为 0。 | 13/15 - 补充目标已有 EPS/PNG digitized reference CSV；仍不是作者原始 plotting data，且部分复平面 panel 以图源点云对照为主。 | 90 | digitized_curve |

## 物理特征断言（T001 Fig. 2）

Fig. 2 target 已声明 4 条机器可查的 `physics_assertions`（证据在
`outputs/checks/fig2_boundary_perturbation.json` 与排序连线复现图）：

| 断言 | 层级 | 状态 |
| --- | --- | --- |
| t1 = 22/15 处首键脱耦、精确穿零 | analytic | passed |
| t1 ≈ 1.025 处 wiggle 最低 0.003，近零不触零 | numeric | passed |
| [1.0, 1.2] 的真实模长交叉按分支连线画成穿越 | line_contract | passed |
| 原文 Fig. 2(d) 用排序连线把交叉画成弹开 | alignment | source_figure_artifact |

`source_figure_artifact` 表示物理层通过、原图自身失真：发布图按物理分支连线渲染，
原图的排序连线样式用我们自己的数据单独复现存证，不扣物理分。

## 结论

所有评分 target 现在都接入了原文图源 digitization：`outputs/checks/all_digitized_curves.json` 记录 5 个 target、15 个 panel，目标级 mismatch count 为 `0`。这已经消除了“缺原图曲线参考”的主要 blocker。

评分模型已把 digitized-curve targets 判到 `complete_reproduction`，但这仍不能说成 100% 或 author-data 级复现：这些 reference 来自 EPS/PNG digitization，不是作者原始 plotting data，也还没有做逐像素版式对齐。

## 论文评测字段

| 数值图/表/面板 | Critical | Role | Artifact pass | Data-backed | Manual interventions | Failure type | Reference comparison | Generated data provenance | Formula gate |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| Fig. 2 open-boundary spectrum | true | main_claim | true | true | 0 | none | digitized_curve | independent_numerics | verified |
| Fig. 3 GBZ and skin localization | true | main_claim | true | true | 0 | none | digitized_curve | independent_numerics | verified |
| Fig. 4 non-Bloch winding number | true | main_claim | true | true | 0 | none | digitized_curve | analytic_reference | verified |
| Fig. 5 nonzero t3 topology | true | supporting | true | true | 0 | none | digitized_curve | independent_numerics | verified |
| Supplemental spectra | false | auxiliary | true | true | 0 | none | digitized_curve | independent_numerics | verified |
