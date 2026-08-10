# Consistency Report

## 总结

- 目标覆盖：15/15 数值或公式目标
- 科学检查：15/15 passed
- 公式门禁：8/8 verified
- 隔离运行：`1807.10084-paper-exact-v2` attested，0 次禁止访问
- 注册像素证据：T006 scientific region passed
- 待补像素证据：T002、T003、T005、T009–T014
- 待补独立评审：T001–T015

## 逐目标一致性

| Target | 论文对象 | 科学结论 | 像素状态 | 证据 |
| --- | --- | --- | --- | --- |
| T001 | Main Fig. 1 levels | 公式能级/方向共振通过 | 不适用，按精确能级验收 | `outputs/checks/target_checks.json#T001` |
| T002 | Main Fig. 2 | 方向选择 1PB 通过 | 待 RenderContract | `outputs/data/main_fig2_correlations.csv` |
| T003 | Main Fig. 3(a-c) | 2PB/PIT、判据、分布通过 | 待 RenderContract | `outputs/data/main_fig3_correlations.csv` |
| T004 | Main Fig. 3(d) | 二/三光子方向共振通过 | 不适用，按精确能级验收 | `outputs/checks/target_checks.json#T004` |
| T005 | Main Fig. 4(a-c) | 方向选择 1PB/2PB 通过 | 待 RenderContract | `outputs/data/main_fig4_correlations.csv` |
| T006 | Supp. Fig. S1 | Fizeau 线性关系通过 | 科学区 82.2364；SSIM 0.9732 | `outputs/checks/pixel_evidence.json` |
| T007 | Supp. Fig. S2 | 非旋转 1PB/2PB 能级通过 | 不适用，按精确能级验收 | `outputs/checks/target_checks.json#T007` |
| T008 | Supp. Fig. S3 | 8 对、16 个方向能级图全部通过 | 不适用，按精确能级验收 | `outputs/checks/target_checks.json#T008` |
| T009 | Supp. Fig. S4 | 弱驱动 1PB/PIT 通过 | 待 RenderContract | `outputs/data/supp_fig_s4_correlations.csv` |
| T010 | Supp. Fig. S5 | 强驱动多光子判据通过 | 待 RenderContract | `outputs/data/supp_fig_s5_correlations.csv` |
| T011 | Supp. Fig. S6 | 数值与弱驱动解析式一致 | 待 RenderContract | `outputs/data/supp_fig_s6_analytic_numeric.csv` |
| T012 | Supp. Fig. S7 | 多转速方向位移通过 | 待 RenderContract | `outputs/data/supp_fig_s7_rotation_sweep.csv` |
| T013 | Supp. Fig. S8 | 6.6 kHz 非互易效应通过 | 待 RenderContract | `outputs/data/supp_fig_s8_6p6khz.csv` |
| T014 | Supp. Fig. S9 | 29/58 kHz 完整案例通过 | 待 RenderContract | `outputs/data/supp_fig_s9_correlations_29khz.csv` |
| T015 | Supp. Table S2 | 8 行允许/禁止组合精确通过 | 不适用，按表格语义验收 | `outputs/checks/supp_table_s2_check.json` |

“待 RenderContract”不是科学失败：独立数组和目标检查已经通过，但当前自由排版重绘不具备同像素坐标系，不能进入主像素均值。
