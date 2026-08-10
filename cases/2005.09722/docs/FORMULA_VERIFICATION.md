# Formula Verification

Machine-readable gate: `outputs/checks/formula_verification.json`。10/10 张公式卡 numeric-open，0 张关闭。

| Formula | Role | Gate | Verification |
| --- | --- | --- | --- |
| EQ001 | 周期最近邻哈密顿量 | verified | FFT 传播与 dense `expm` 单元测试一致 |
| EQ002 | QSD stochastic equation | source_only | 逐项追溯 Main Eq. (1)，正交残差检查 |
| EQ003 | QSD/QSDc Trotter update | source_only | 补充材料给出对角因子、sigma switch、QR 和 dt |
| EQ004 | Gaussian interval entropy | verified | Néel product state 极限为零熵 |
| EQ005 | CFT entropy fit | source_only | 线性最小二乘实现论文 Eq. (2)；拟合窗未完整公布 |
| EQ006 | mutual information/cross ratio | verified | product-state MI 为零，cross ratio 解析检查 |
| EQ007 | connected correlations | verified | Wick identity 与 tau=0 两时表达式单元测试 |
| EQ008 | event-driven QJ | verified | occupied-orbital 更新与论文 covariance update 一致至 5e-13 |
| EQ009 | random hopping | source_only | 二值键分布和单位时间刷新来自补充材料 |
| EQ010 | BKT transforms | source_only | gamma_c、alpha、g(L) 和两组坐标逐项实现 |

`source_only` 表示论文明确给出、且所有检查通过，但没有另一条独立解析推导把它升级为 `verified`；它仍允许数值化，不代表公式不可信。
