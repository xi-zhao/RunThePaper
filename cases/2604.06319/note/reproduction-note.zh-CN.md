# QC05 复现记录

按发表版附录重建 QPU、量子存储和链路账本。1000 逻辑比特时，基准相对 STQM 和 RAQM 的物理比特比分别为 59.56 和 138.58。RSA 的两组关键配置重算为约 38.1 万和 19.0 万物理比特。 [论文](https://doi.org/10.1088/1367-2630/aeb71b)

## 复现范围

整篇为部分复现。原始编译电路、逐门调度及噪声记录缺失。表 6 周期标签和非局部耦合器权重仍有差异。

[运行方法](../docs/NUMERICAL_METHODS.md) · [推导](../docs/DERIVATION.md) · [数值证据](../outputs/checks/numerical-checks.json)
