# Method Trace

| Method | 输入 | 输出 | 实现 | 检查 | 状态 |
| --- | --- | --- | --- | --- | --- |
| MTH_LINDBLAD | 论文 Hamiltonian、`γ`、驱动、Fock cutoff | 稳态密度矩阵 | `src/nonreciprocal_pb/steady_state.py` | 迹、Hermiticity、最小本征值、残差、cutoff 收敛 | verified |
| MTH_OBSERVABLES | 稳态密度矩阵 | `P(n)`、`g²`、`g³`、PB/PIT 判据 | `src/nonreciprocal_pb/observables.py` | 15 个 target checks 与解析极限 | verified |
| MTH_RENDER | 冻结 CSV 或公式能级 | 数值图/能级图 | `src/nonreciprocal_pb/rendering.py` | dataset-to-figure contract | verified |
| MTH_RENDER_CONTRACT | 冻结 CSV 哈希、样式合同 | 同几何科学图 | `src/nonreciprocal_pb/render_contract.py` | 数组哈希、画幅、像素证据 | T006 verified；其余 pending |

数值方法没有调用论文作者代码，也没有从作者图像反推曲线坐标。原图只在数值运行之后用于可视比对和 RenderContract 样式校准。
