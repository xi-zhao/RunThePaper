# 复现方法札记 / Lessons from the reproduction

**把评分公式单独验收。** 对同均值的常数估计图，分别计算正文的 SSIM 和公开实现的变体。先确认方差项与稳定常数，再比较两种策略的预算曲线。相同地图在两种计分下也可能改变算法排序。

**分开调参和检验。** 对每个预算用独立种子选择参数，再在新的 50 条轨迹上评估。报告只在两条曲线均有观测支撑的误差范围内计算收益，同时保留反向插值和首次达标的差别。

**区分公开帧与历史模型。** 原始相机帧足以训练新分类器并比较相位，历史拟合树和选帧记录决定能否精确回放已刊面板。[本篇的数值约定](NUMERICAL_METHODS.md)

Check the score on controlled maps before comparing algorithms. Separate tuning from held-out evaluation, and restrict inverse budget interpolation to the observed range. Keep the availability of raw measurements and the availability of the historical estimator as distinct checks.
