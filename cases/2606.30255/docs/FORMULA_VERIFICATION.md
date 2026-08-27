# Formula Verification

## 结论

冻结范围依赖的 7 张 equation card 全部达到 `verified`，公式门结果为 `passed`，0 finding。每个数值目标都绑定同一组已核验公式和 `MTH-SCANS` 方法卡。

机器证据：

- `outputs/checks/formula_symbolic_checks.json`
- `outputs/checks/formula_verification.json`
- `outputs/checks/target_readiness/*.final_reproduction.json`

## Gate Summary

| Formula card | 论文来源 | 数值角色 | Gate | 独立检查 |
| --- | --- | --- | --- | --- |
| `EQC-MEASUREMENT` | Eq. (7) | 偏振测量 ket | `verified` | \(\sin^2\theta+\cos^2\theta=1\) |
| `EQC-SOURCE-STATE` | Eq. (18) | 两光子纯态 | `verified` | \(w+(1-w)=1\) |
| `EQC-DENSITY` | Eq. (20) | 白噪声混态 | `verified` | 厄米、迹为 1、半正定 |
| `EQC-BORN` | Eqs. (8)–(9) | \(P_{++}\) | `verified` | singlet 化为 \(\frac12\sin^2(\alpha-\beta)\) |
| `EQC-WIGNER` | Eq. (5) | \(\mathcal W=P_{ab}+P_{bc}-P_{ac}\) | `verified` | 逐点恒等式误差 0 |
| `EQC-SINGLET-LIMIT` | Eqs. (10)–(13) | 对称/非对称解析极限 | `verified` | \(-1/8\) 与 \((1-\sqrt3)/4\) 精确通过 |
| `EQC-FIDELITY` | Eq. (21) | singlet fidelity | `verified` | 从舍入后的 \(w,v\) 独立重算 |

## 方法边界

- Figure 3 扫描相对间隔 \(\phi\)。
- Figure 4 横轴 \(\Theta\) 是中间设置 \(b\) 的绝对角，因此基组起点为 \(\Theta-\phi\)。
- Figure 5 上固定 Alice、扫描 Bob；下固定 Bob、扫描 Alice。
- 投影测量具有 180° 周期性，所有四个目标的数值周期误差均小于 \(10^{-15}\)。

## 已记录的论文舍入效应

正文只报告两位小数的拟合参数。由这些数值重算的 fidelity 与正文值之差为：

| Target | 重算值 | 正文值 | 绝对差 |
| --- | ---: | ---: | ---: |
| `T-FIG003` | 0.985000 | 0.985 | 0 |
| `T-FIG004` | 0.972700 | 0.978 | 0.0053 |
| `T-FIG005A` | 0.897003 | 0.896 | 0.0010 |
| `T-FIG005B` | 0.917650 | 0.914 | 0.0036 |

这些差值小于预先记录的 `0.006` 舍入容差，不需要修改论文参数。

## 复验命令

```bash
python case/2606.30255/scripts/verify_formulas.py
PYTHONPATH=PRAgent-workflow python PRAgent-workflow/scripts/check_formula_gate.py case/2606.30255 --write
```
