# 证据索引 / Evidence map

| 报告结论 | 实现或定义 | 生成数据／检查 |
|---|---|---|
| CSS 与元校验 | [二元构造](../code/preparation/src/generate_algebra.py) | [algebra](../outputs/data/algebra.json)、[矩阵](../outputs/data/code_matrices.npz) |
| 距离及上界 | [距离算法](../code/base/scripts/generate_distance.py) | [distance](../outputs/data/distance.json)、[额外见证](../outputs/data/extra-distances.json) |
| 制备 MAP/MLE 接受率 | [decoder](../code/preparation/src/prep_decoder.py)、[固定配置](../code/preparation/config/experiment.json) | [结果](../outputs/data/preparation/results.json)、[分布](../outputs/data/preparation/tables.npz)、[线路](../outputs/data/preparation/programs.json) |
| 门序与低阶故障 | [扫描](../code/preparation/src/tri_order_scan.py)、[故障审计](../code/preparation/src/fault_audit.py) | [门序结果](../outputs/data/gate-order-scan.json)、[故障结果](../outputs/data/fault-audit.json) |
| 原图差距 | [比较与版本](COMPARISONS.md) | [聚合残差](../outputs/checks/preparation-summary.json) |
| 当前目标与记录 | [量化口径](QUANTIFICATION.md) | [逐项原生判断投影](../outputs/checks/completion_assessment.json)、[来源散列](../outputs/checks/publication_provenance.json) |

公开源图比较仅保留必要的有限比较板与聚合残差；不分发原始论文、独立原图或读图点集。重新计算生成结果不需要作者原数组。重新得到同一读图误差则需要在指定 v1 原图上独立提取，并说明提取不确定性。
