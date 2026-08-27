# Similarity Scorecard

## Case Score

- Overall score：`97.5 / 100`
- Similarity level：`complete_reproduction`
- Status：`passed`
- Final reproduction ready：`true`
- Critical targets：`4 / 4`
- Physics assertions：`16 passed / 0 failed`

科学分只衡量公式、数值、目标特征和冻结范围覆盖；像素分单独报告。

## Scoring Model

每个目标满分 100：

- feature match：50；
- numeric closeness：35；
- paper-scope coverage：15。

四个目标权重均为 1。所有目标均为 `paper_exact`、`final_reproduction`、`author_data` reference 和 `independent_numerics` provenance，因此没有证据上限折扣。

## Figure Scores

| Figure/Panel | Feature | Numeric | Scope | Score | 主要理由 |
| --- | ---: | ---: | ---: | ---: | --- |
| Figure 3 theory | 50/50 | 33/35 | 15/15 | 98 | 5/5 序列；W \(r=0.99966\)，RMSE 0.01113 |
| Figure 4 theory | 50/50 | 35/35 | 15/15 | 100 | 全局旋转不变量；W RMSE 0.00712 |
| Figure 5 top theory | 49/50 | 31/35 | 15/15 | 95 | W \(r=0.98852\)，极值相位差 5° |
| Figure 5 bottom theory | 50/50 | 32/35 | 15/15 | 97 | W \(r=0.99583\)，极值相位差 3° |

## Evaluation Metadata

| Target | Stage | Parameters | Critical | Role | Artifact | Data | Manual interventions | Failure |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| `T-FIG003` | final_reproduction | paper_exact | true | main_claim | pass | backed | 0 | none |
| `T-FIG004` | final_reproduction | paper_exact | true | main_claim | pass | backed | 0 | none |
| `T-FIG005A` | final_reproduction | paper_exact | true | main_claim | pass | backed | 0 | none |
| `T-FIG005B` | final_reproduction | paper_exact | true | main_claim | pass | backed | 0 | none |

## Pixel Lane

| Target | Axis bbox IoU | Ink proximity | Pixel score | Contract |
| --- | ---: | ---: | ---: | --- |
| `T-FIG003` | 0.9920 | 0.6568 | 81.58 | passed |
| `T-FIG004` | 0.9920 | 0.6809 | 83.04 | passed |
| `T-FIG005A` | 0.9908 | 0.7286 | 85.30 | passed |
| `T-FIG005B` | 0.9920 | 0.7320 | 85.56 | passed |

像素总分为 `83.87`。源图包含范围外实验标记，独立图只包含理论线，因此未把逐像素相同作为科学条件。

## Why The Score Is Below 100

Figure 3 的单项概率与实验数据存在论文明确讨论的损耗偏置；Figure 5 的最简密度矩阵模型也没有探测器级损耗与计数噪声。这些差异在 author-data 数值接近度中扣分，但不影响论文理论曲线、解析极限和冻结范围覆盖。

机器记录：`outputs/checks/similarity_scorecard.json`。
