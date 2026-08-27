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

## Target-level independent closure

公式卡保留上述来源等级，不把论文给出的式子伪装成独立推导。另一个更窄的 target-level evaluator 用不同实现检查已接受的生成结果：

- EQ002/EQ003：在 `L=200,400,800` 上做 NumPy backend cross-check，相关矩阵和半链熵差均为 0，最大正交残差 `1.11e-15`。
- EQ005：用解析生成的 CFT 数据回收 `c=1.75` 和截距 `0.37`，`R^2=1`。
- EQ009：随机跃迁传播子的最大 unitarity residual 为 `1.78e-15`。
- EQ010：对 attested CSV 独立重算 BKT 两组变换，172 个有限值全部通过。
- T033–T036：分别用零变化率、投影恒等式、Gauss-Hermite 短时导数和 Legendre 积分检查解析主张。

因此 `source_only` 仍是公式卡 provenance，目标的 `formula_gate=verified` 则表示其当前缩尺度/解析 artifact 已通过独立机器检查；两者服务不同问题。完整记录见 `outputs/checks/final_disposition_evidence.json`。
