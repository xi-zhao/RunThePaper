# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| `exact_match` | 4 | 论文参数、公式、目标结构和全部理论序列均独立重算通过 |
| `feature_match` | 0 | 没有只停留在定性特征层的目标 |
| `partial_match` | 0 | 没有部分通过的冻结目标 |
| `input_match_only` | 0 | 没有只有输入一致而输出未验证的目标 |
| `not_in_scope` | 10 | 表格、示意/装置子图和实验序列 |

## Per-Target Consistency

| Target | Paper item | Level | Author-data evidence | Pixel evidence | Difference and interpretation |
| --- | --- | --- | --- | --- | --- |
| `T-FIG003` | Figure 3 theory | `exact_match` | W RMSE 0.01113, \(r=0.99966\) | 81.58, contract passed | 单项概率存在论文已说明的探测损耗偏置；W 和相位精确保持 |
| `T-FIG004` | Figure 4 theory | `exact_match` | W RMSE 0.00712，均值误差 0.00318 | 83.04, contract passed | 理论 W 为常数；实验点的小幅波动属于测量噪声 |
| `T-FIG005A` | Figure 5 top theory | `exact_match` | W RMSE 0.06313, \(r=0.98852\) | 85.30, contract passed | 最小值相位与作者数据相差 5°；最简模型不含探测器损耗 |
| `T-FIG005B` | Figure 5 bottom theory | `exact_match` | W RMSE 0.04022, \(r=0.99583\) | 85.56, contract passed | 最小值相位与作者数据相差 3°；最简模型不含探测器损耗 |

## Invariants

- 所有密度矩阵厄米、迹为 1、半正定。
- 所有 Born 概率位于 \([0,1]\)。
- `wigner = p_ab + p_bc - p_ac` 的生成数据误差为 0。
- 180° 投影周期误差小于 \(10^{-15}\)。
- 理想对称极限 \(-1/8\) 和非对称极限 \((1-\sqrt3)/4\) 达到机器精度。
- 每个目标都有 5/5 可见理论序列、721 个角度点和独立数据 provenance。

## Source Boundaries

作者发布的实验 TSV 只用于生成后的对照。源图像素只用于排版、注册和像素证据；没有曲线描点、图像数字化、追踪或源面板复制进入生成数据。
