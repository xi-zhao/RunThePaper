# 复现方法札记 / Lessons from the reproduction

**同时核对理想门和误差导数。** 两种空闲脉冲在零噪声时等价到全局相位，共享失谐下的一阶响应却不同。保持相同的随机序列和噪声实例，只改脉冲方向，可以直接量出它对随机基准方差的影响。

**锁定噪声时钟。** 分段噪声的独立性与更新时间同样进入二阶矩计算。给出跨脉冲的同步时钟，并单列每种脉冲等分的对照，才能解释表 III 的两个数值。

**保留可识别性边界。** 图中相关系数和跨序列方差是汇总量，原始联合读出与时序仍决定能否重算不确定度和归因。[本篇的数值约定](NUMERICAL_METHODS.md)

Check both the ideal gate and its error derivative. Change one physical convention at a time while holding sequence and noise draws fixed. Record the noise update clock and distinguish aggregate agreement from a replay of the hardware trials.
