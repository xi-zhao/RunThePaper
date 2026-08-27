# Formula Verification

机器结果：`outputs/checks/formula_verification.json`。

## Gate Summary

| Formula | 数值角色 | Gate | 核验依据 |
| --- | --- | --- | --- |
| EQC001 | 有限程无序 Hamiltonian | verified | arXiv TeX 来源 + hopping 方向检查 |
| EQC002 | `M=2` 单格点转移矩阵 | verified | 从差分方程逐项移项，并做随机向量递推残差检查 |
| EQC003 | Lyapunov 谱与 clean `beta` 极限 | verified | 周期 QR；clean limit 与 `log|beta|` 对照 |
| EQC004 | OBC Thouless 势 | verified | 论文来源 + 有限谱 logdet 检查 + OBC 密度重合度 `0.806917` |
| EQC005 | PBC Thouless 势 | verified | 论文来源 + twist winding 交叉检查 + PBC 密度重合度 `0.849765` |
| EQC006 | essential LE 与迁移边 | verified | 中央指数符号分类和分支规则核验 |
| EQC007 | `nu=M-n_positive` | verified | 论文公式 + 独立 twisted determinant 数值检查 |
| EQC008 | Anderson 局域比例 `alpha` | verified | 论文定义 + 有界性和单调趋势检查 |

## 数值 sanity checks

- clean-limit 四个 LE 与 `log|beta|` 最大绝对误差：`7.43e-5`。
- 单步转移矩阵与原差分方程的残差：`1.50e-16`。
- 8 张公式卡全部 numeric-open 且具独立推导、极限或数值 sanity 证据；无
  closed/unknown 公式进入数值代码。

## 定理边界

EQC004 和 EQC005 是论文核心定理。本 case 没有把“未重写一份完整一般性证明”
误记成失败，而是在目标参数区间做了独立的可证伪核验：有限谱 logdet、OBC/PBC
独立对角化密度和直接 twist winding 均与 Lyapunov 实现相符。因此数值使用门记为
`verified`。这里的 `verified` 只表示“足以支撑本次复现区间内的数值化”，不声称
给出了超出论文范围的新一般性定理证明。

## Open Details

- arXiv v1 没有报告 transfer length 或 QR interval；正式补充材料确认使用周期 QR，
  仍未给出 interval。
- Fig. 5(b) 的 ensemble 和 quadrature 细节未公开。

重跑 gate：

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/2507.09447 --write
```
