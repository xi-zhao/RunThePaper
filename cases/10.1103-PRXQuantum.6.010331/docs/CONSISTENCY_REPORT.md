# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact analytic-form match | 1 | Fig. 15 使用 Appendix L 的全部公开系数；不等于未公开底层轨迹的精确数值曲线。 |
| paper-subset formula calculations | 5 | T002-T004、T006、T008 的公开公式/参数子集通过。 |
| independent Hamiltonian numerics | 1 | T005 的三套公开 CZ 控制通过闭合、泄漏和相位检查。 |
| explicit physical reconstruction | 2 | T007 明示滤波约定；T009 明示几何/ramp 替代参数。 |
| blocked exact curves | 10 figure/table groups | 缺 PSD、完整模型参数、几何、精确脉冲或电路元数据。 |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Remaining difference | Cause |
| --- | --- | --- | --- | --- | --- |
| T001 | Fig. 15 | exact analytic-form / partial curve | `universal_response.json` | 强度响应在 `x≈1.5,2.5` 的小峰缺失 | Appendix-L 是近似拟合；底层轨迹未公开 |
| T002 | Fig. 6(a) | envelope / physics match | `fig6a_scaled_response.json` | 强度小峰缺失；未覆盖 PSD 与误差直方图 | 精确轨迹和原始 PSD 数组未公开 |
| T003 | Fig. 1(f)/Fig. 7 | formula subset | `formula_theory_targets.json` | 绝对频率/运动项缺失 | PSD 与 Doppler variance 未公开 |
| T004 | Fig. 8 | anchor-constrained reconstruction | `formula_theory_targets.json` | 总误差和 `n=44` 最优点未独立恢复 | lifetime/PSD/temperature/electric-field arrays 未公开 |
| T005 | Fig. 9(a,b) | independent physics calculation | `formula_theory_targets.json` | Fig. 9(c) 未覆盖；Fromonteil 离散 variant 身份为重建 | 实验 noise amplitude 与目标 variant 标识未公开 |
| T006 | Fig. 10 | exact analytic filter | `formula_theory_targets.json` | 绝对 decay/data 曲线缺失 | 数值 PSD 和实验点未公开 |
| T007 | Fig. 12 | disclosed transfer reconstruction | `formula_theory_targets.json` | filtered PSD/full-model 曲线缺失 | PSD、full model 和传递 convention 未完整公开 |
| T008 | Fig. 17 | analytic formula subset | `formula_theory_targets.json` | full quadratic circuit inset 缺失 | exact circuit length/recovery realization 未公开 |
| T009 | Fig. 11 | independent physical reconstruction | `formula_theory_targets.json` | 非 paper-exact 曲线 | geometry、C6/r6、exact ramps 未公开 |
| D001 | Fig. 15 direct diagnostic | partial | `direct_response_diagnostic.json` | 响应 NRMSE `0.084-0.411` | 被引通用脉冲不等于未公开目标轨迹 |

## Checks

- 公式门：13/13 open，0 closed。
- 物理项目：9 targets、9 datasets、9 rendered figures，0 errors/warnings。
- 单元测试：21/21 passed。
- 像素输入审计：passed；计算源码中 0 个 image-read 调用，对比渲染器中
  2 个 `plt.imread` 调用被隔离记录。
- 数据来源：`analytic_reference`、`formula_numerics`、
  `independent_hamiltonian_numerics` 或 `independent_many_body_numerics`；
  不含 digitized/source-panel provenance。
