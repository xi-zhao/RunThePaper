# QC26 复现记录

复算有限差分滤波器、CPMG 与 DPSS。99 个共同频点和双谱图 13 组三轴读数的重分析恢复约 7 与 11 kHz 峰。两平台的 DPSS 可见标记差分别为 0.0240 和 0.0109 Hz RMS。 [论文](https://doi.org/10.1103/physrevapplied.14.024021)

## 复现范围

整篇为部分复现。实机读出与谱标定仍缺。主入口复算可脱离参考曲线运行的单音和脉冲滤波块。

[运行方法](../docs/NUMERICAL_METHODS.md) · [推导](../docs/DERIVATION.md) · [数值证据](../outputs/checks/numerical-checks.json)
