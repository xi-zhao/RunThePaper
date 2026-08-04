# Formula Verification

本文件说明哪些公式获准进入冻结理论目标。机器可读结果位于
`outputs/checks/formula_verification.json`；完整推导见
`DERIVATION_TRACE.md`，由 equation cards 生成的快照见 `DERIVATION.md`。

运行：

```bash
python private validation harness/scripts/check_formula_gate.py case/2606.30255 --write
```

## Gate Summary

公式 gate 状态为 `passed`：6 张 equation cards 全部 `verified`，
`trusted_for_numerics=6`，`blocked_for_numerics=0`，未留 open question。

| Formula | Role | Gate | Main verification |
| --- | --- | --- | --- |
| EQC001 | 偏振测量态 \(|m(x)\rangle\) | verified | 论文 Eq. (7) 来源明确且 \(\sin^2x+\cos^2x=1\)。 |
| EQC002 | 含白噪声的两光子密度矩阵 | verified | 论文 Eqs. (18),(20)；迹为 1，eigenvalues 对全部论文 \(v\) 非负。 |
| EQC003 | 联合 Born 透射概率 | verified | 从 EQC001/002 独立收缩；singlet 极限严格回到论文 Eq. (9)。 |
| EQC004 | Alice/Bob 三设置角度几何 | verified | 对称时相对角为 \(\phi,\phi,2\phi\)，非对称时为 \(15^\circ,15^\circ,45^\circ\)。 |
| EQC005 | Wigner observable | verified | 论文 Eqs. (5),(10)；经典表化简为 \(p_3+p_6\geq0\)。 |
| EQC006 | 对称与非对称理想极限 | verified | 直接得到 \(-1/8\) 与 \((1-\sqrt3)/4\)。 |

## Independent Numerical Form

生成路径计算

\[
\operatorname{Tr}\left[\rho\left(\Pi_x\otimes\Pi_y\right)\right].
\]

核验路径单独实现

\[
v\left(\sqrt w\sin x\cos y-\sqrt{1-w}\cos x\sin y\right)^2
+\frac{1-v}{4}.
\]

二者没有共享概率实现；四个 target 的逐点最大差不超过
\(5.56\times10^{-16}\)，从而把 tensor-product 顺序、相位符号和
角度映射纳入可执行检查。

## Closed Or Unclear Formulas

| Formula | Reason | Numerical consequence |
| --- | --- | --- |
| None | 所有冻结目标依赖项均已验证。 | 无数值 gate blocker。 |

## Scope Boundary

论文有关 detector efficiency、公平采样、perfect anticorrelation
loophole 和实验 coincidence normalization 的表达式用于全文理解，
但不为冻结 theory-only 曲线提供生成数据。它们没有被伪装成已复现的
实验方法。
