# Consistency Report

## 汇总

| Level | Count | Meaning |
| --- | ---: | --- |
| feature_match | 6 | 公式、论文参数、数值不变量与完整子图范围均通过。 |
| not_in_scope | 1 | Supplement Fig. S1 是纯概念映射图。 |

## 逐目标

| Target | Paper item | Level | 关键证据 |
| --- | --- | --- | --- |
| T001 | Main Fig. 1(a) | feature_match | 初态 Husimi 峰值与 1 的差 `6.66e-16` |
| T002 | Main Fig. 1(b) | feature_match | `tau=N^(-2/3)` 独立演化，概率范围合法 |
| T003 | Main Fig. 1(c) | feature_match | 闭式/数值最大差 `2.27e-13`；末态谱 `(400,20,20)` |
| T004 | Main Fig. 1(d) | feature_match | 本征残差 `2.29e-13`；解析轴投影重叠 `0.9999999999999993` |
| T005 | Main Fig. 2(a) | feature_match | 峰值 `146.4517`；三项印刷锚点最大差 `4.55e-4` |
| T006 | Main Fig. 2(b) | feature_match | 投影秩与归一化通过；最大本征残差 `2.02e-13` |

T006 的源图在简并区选择了未声明的本征矢规范，因此只比较规范不变的领先空间和
本征值，不把逐像素系数差当作科学失败。

## 论文内部一致性

`DISC-INITIAL-K-AXIS`：显式 ket 的方差为零轴是 `J_x` 与 `K_z`，不是正文所写
`J_x` 与 `K_y`。当前为 `inconclusive`，没有生成 `paper_error_candidate`。
