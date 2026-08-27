# 相似度评分卡：2103.03074

## 总分

- Overall score: `70.0/100`
- Similarity level: `numerical_feature_reproduction`
- 解释：big-batch 方法的统计特征已经清楚出现，但本地复现规模是 18 qubit，不是原论文的 53 qubit Sycamore 张量网络收缩。

## 单图评分

| 数值图/表/面板 | Weight | 数值特征吻合度 | 关键数值接近度 | 原文目标覆盖度 | Score |
| --- | ---: | --- | --- | --- | ---: |
| Fig. 2 depth-20 XEB | 1.0 | 48/50 - Porter-Thomas 分布和 post-selection XEB 上升特征都出现。 | 25/35 - XEB 曲线与理论形状接近，完整 batch XEB 接近 0。 | 2/15 - 本地是 18 qubit 特征复现，不是 53 qubit Sycamore 原始规模。 | 70 |
| Fig. 5 depth-14 XEB | 1.0 | 48/50 - depth-14 的概率分布和 post-selection 趋势出现。 | 26/35 - 曲线形状和 -log(fraction) 关系更接近，误差较小。 | 2/15 - 仍然是小规模独立复现，没有重跑论文级张量网络。 | 70 |
| Conditional probability method | 0.5 | 45/50 - 固定 closed bits、枚举 open bits 的 big-batch 机制闭环。 | 22/35 - 条件概率归一化和直接 amplitude lookup 校验通过。 | 3/15 - 方法闭环但不是大规模工程实现。 | 70 |

## 结论

big-batch 方法的统计特征已经清楚出现，但本地复现规模是 18 qubit，不是原论文的 53 qubit Sycamore 张量网络收缩。

这张评分卡的目标是让读者看到每一张数值图为什么得分，而不是只看到一个总分。

## 论文评测字段

| 数值图/表/面板 | Critical | Role | Parameter match | Artifact pass | Data-backed | Failure type |
| --- | --- | --- | --- | --- | --- | --- |
| Fig. 2 depth-20 XEB | true | main_claim | reduced_scale | true | true | insufficient_compute |
| Fig. 5 depth-14 XEB | true | main_claim | reduced_scale | true | true | insufficient_compute |
| Conditional probability method | false | method_validation | reduced_scale | true | true | insufficient_compute |

## Author closure v6 (fresh review requested)

The table above is the historical 18-qubit feature score and is not the final
scientific disposition.  The current author baseline covers all 17 targets
with exact Dryad circuit ingestion, analytic rederivations, a bounded
paper-scale tensor-network attempt, one generic streaming full-state/sampling
runner, a local complex64 benchmark, and an attested minimal-input run.  It
deliberately does not promote reduced smoke evidence to paper-scale coverage or
assign paper-error verdicts.  The machine-readable current evidence is
`outputs/checks/similarity_scorecard.json` plus
`outputs/data/scientific_closure/T001.json` through `T017.json`.
