# QC18 复现记录

复算 9 张图的 32 个数值面板。离子阱头两次返回概率为 0.743 和 0.544，落在论文所报误差内，93 倍口径重算为 92.73 倍。独立闭环控制比较了单比特、双比特和相位设计。 [论文](https://doi.org/10.1103/physrevapplied.21.014012)

## 复现范围

整篇为部分复现。原闭环参数和逐次离子读出缺失。高斯似然分母的因子差异需和闭环模型约定一并解读。

[运行方法](../docs/NUMERICAL_METHODS.md) · [推导](../docs/DERIVATION.md) · [数值证据](../outputs/checks/numerical-checks.json)
