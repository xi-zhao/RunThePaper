# 这次复现学到了什么

绘图输出采样与积分器内部步长不同。极短时间的浅谷可以由解析初始斜率确认，却被较稀的输出网格跳过；提升积分精度不能自动增加绘图采样点。本例约 0.14% 的浅谷不改变主要加速效应。

印刷参数精度、指定稳态和速度单位也应逐项核对。保留印刷版与按声明稳态重建版，比用一套经过调整的参数覆盖原结果更容易检查。比较时应同时交代数值差异和它对物理结论的实际影响。

Distinguish printed-parameter rounding, solver accuracy, output sampling, and plotting units. A tiny local feature can coexist with correctly reproduced main physics; both observations belong in the report.
