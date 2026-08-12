# Formula Verification

## Gate Summary

全部 9 张公式卡均允许进入数值通道；其中 EQC001–EQC008 为论文公式或公开标量的独立实现，EQC009 是明确标注的标量模式/损耗重建，不冒充作者未公开的矢量 FEM。

| Formula | Scientific role | Gate | Independent check |
| --- | --- | --- | --- |
| EQC001 | 双源 N00N 输入态 | open | 任意 `b in [0,1]` 和相位下归一化 |
| EQC002 | 单光子 MZI 幺正矩阵 | open | 全相位网格 `max ||U†U-I|| < 6e-16` |
| EQC003 | 对称二光子 Fock 提升 | open | 提升矩阵幺正误差 `<1e-15`；Eq. (4) 两个极限成立 |
| EQC004 | 部分相干密度矩阵 | open | Hermitian、trace-one、正半定 |
| EQC005 | 经典 MZI 转移率 | open | 每个输入端口的两输出概率和为 1 |
| EQC006 | 反射率依赖 HOM 可见度 | open | `V(1/2)=1`，`V(0)=V(1)=0` |
| EQC007 | 高斯 HOM 延迟模型 | open | 半高宽恒等式；多个带宽约定并列报告 |
| EQC008 | 损耗修正亮度 | open | 独立量纲/算术复核得到 `2.309021589e8 pairs/s/mW` |
| EQC009 | 标量模式与金属重叠损耗 | open as reconstruction | 有效折射率物理、场归一化、损耗随 gap 单调下降 |

## Closed Or Unclear Formulas

没有公式门被关闭。存在两个解释边界，但没有被静默选定：

- HOM 的 `71.9 fs` 未声明是哪种高斯宽度约定；代码同时输出 `49.92 nm` 和 `70.64 nm` 两种映射。
- 论文没有公开矢量 FEM 的完整材料表、网格和边界条件；EQC009 只能支持趋势级重建。

机器证据由 `EQUATION_CARDS.json`、`outputs/checks/feature/target_checks.json` 和 Harness 公式门共同给出。
