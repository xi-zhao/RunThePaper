# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | 没有作者原始数值数据，也未运行论文原尺度 |
| feature_match | 31 | 每个数值轴均通过预声明的缩尺度科学检查 |
| partial_match | 0 | target 级检查没有部分失败 |
| blocked | 0 | 无数值轴被静默跳过 |
| not_in_scope | 2 | Main Fig. 1(a,b) 为示意/概念图 |

## Per-Target Consistency

| Targets | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001-T006 | Main Fig. 1(c-e) | feature_match | `target_checks.json`, `main_fig1_numeric_cde.png` | 有限尺寸拟合不等于论文热力学极限 | L<=96 vs L<=800 |
| T007-T011 | Main Fig. 2(a-c) | feature_match | `target_checks.json`, `main_fig2_abc.png` | BKT collapse 仅为变换与形态验证 | 尺寸不足以定位临界点 |
| T012-T017 | Main Fig. 3(a-d) | feature_match | `target_checks.json`, `main_fig3_abcd.png` | 采样点、尺寸和噪声不同 | L<=96 vs L=400/800 |
| T018-T022 | Supp. Fig. 4(a-d) | feature_match | `target_checks.json`, `supp_figure_qj_abcd.png` | 时间曲线统计噪声更大 | 4-12 trajectories；L=64/96 |
| T023-T024 | Supp. autocorrelation | feature_match | `target_checks.json`, `supp_autocorrelation_ab.png` | 远尾单点不稳定，采用固定窗积分 | L=64、12 trajectories |
| T025 | Supp. random hopping | feature_match | `target_checks.json`, `supp_random_hopping.png` | 曲线较稀疏 | L=64 vs L=200 |
| T026-T031 | Supp. statistics | feature_match | `target_checks.json`, `supp_entropy_statistics.png` | 不能还原细粒度分布 | 192 vs 5000 trajectories |

## Pixel Interpretation

所有 target 都明确记录 `pixel_status=not_applicable`：独立缩尺度随机数据无法与论文原尺度 panel 做一一配准。`comparison-artifacts/` 的对照板用于审查科学形态与覆盖，不作为数值输入或像素分依据。
