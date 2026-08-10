# Formula Verification

机器结果：`outputs/checks/formula_verification.json`，状态 `passed`，8/8 公式卡可用于数值生成。

| Formula | 作用 | Gate | 实现位置 |
| --- | --- | --- | --- |
| EQ001 | Fizeau 频移与方向符号 | verified | `src/nonreciprocal_pb/physics.py` |
| EQ002 | Kerr Hamiltonian 与 Fock 能级 | verified | `src/nonreciprocal_pb/model.py` |
| EQ003 | `U`、`γ`、驱动强度的物理量映射 | verified | `src/nonreciprocal_pb/physics.py` |
| EQ004 | 单光子损耗 Lindblad 方程 | verified | `src/nonreciprocal_pb/steady_state.py` |
| EQ005 | `P(n)`、平均光子数和阶乘关联 | verified | `src/nonreciprocal_pb/observables.py` |
| EQ006 | 弱驱动 `g²/g³` 解析式 | verified | `src/nonreciprocal_pb/observables.py` |
| EQ007 | PB/PIT 与 Poisson 偏离判据 | verified | `src/nonreciprocal_pb/observables.py` |
| EQ008 | 迹约束下的向量化稳态线性方程 | verified | `src/nonreciprocal_pb/steady_state.py` |

关键独立推导：由 `E_n/U=n(1-k+s f)+n(n-1)=0` 得到 `k=n+s f`。Supplement Fig. S3 和 Table S2 的允许/禁止方向组合均从这个条件重新推导，没有读取作者代码或图像坐标。

论文示意图采用精确理想比值 `f=1` 或 `1/2`；数值主方程采用正文打印的 `Ω=58/29 kHz`。两者在数据模型中明确分开，避免把四舍五入后的物理转速误当成理想能级关系。
