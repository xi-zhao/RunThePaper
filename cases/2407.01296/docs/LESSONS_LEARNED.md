# Lessons Learned

## Architecture lessons

- “论文有代码”不等于复现可以读取代码。独立生成通道必须只依赖论文公式、公开参数和自写实现；作者资产只能在隔离的事后比较区出现。
- 一个图级 target 容易掩盖遗漏子图。全文 inventory 必须先细化到 panel，再映射到少量共享科学 target。
- `insufficient_compute` 只能延后执行，不能替代实现。paper-scale config、入口、预计输出、恢复策略和验收条件必须先存在。
- 图像渲染与数值生成应是两个权限不同的通道：前者可以看原图调版式，后者禁止读取原图；数据哈希连接二者。
- 论文也可能错或写得不完整。疑点必须输出两个或更多可证伪解释，不能从原图形状反向选择最像的一种。

## Case-specific findings

- Main Fig. 2(d) 的旧主动证据依赖作者 ED 表；新通道用独立有限 OBC 谱势替代，并扩大为区域扫描。
- Supplement S5 选态能量缺失，S7 正标量语义与 N=935 几何不唯一。这些是科学输入边界，不是绘图问题。
- 非正规谱的最大点误差容易被条件数放大；应同时保留矩阵恒等式、median/p95/max 和残差。
- 谱势的二阶差分会放大采样噪声；上游势、原始密度和仅供显示的裁剪密度必须分开保存。

## Reusable workflow

`inventory → formula cards → code-ready paper profile → isolated smoke → frozen hashes → render → score → fresh review`。这条循环可以用于早期 case 的批量修复，但 lifecycle 晋级仍由权威状态模型裁决。

## New Failure Modes

- `public_projection_ahead_of_authority`：公开投影包含较强结论，但权威 case 未同步对应目标、运行合同和审查状态。
- `author_validation_in_active_score`：作者数组只用于事后比较，却被主动 project/scorecard 当成生成证据。
- `point_probe_substitutes_region`：用少量手选能量点冒充论文声明的二维区域收敛。
- `complex_observable_rendered_as_unspecified_positive_scalar`：公式给出复数，图却没有说明正标量映射。

## Reusable Checks Or Tools

- 全文 panel inventory 与 `implementation_ref` code-readiness gate；
- 配置 SHA、实现 SHA、输出 SHA 三重绑定的 target checkpoint；
- raw/reference/network 禁止访问的 isolated runner；
- RenderContract 输入前后哈希一致性检查；
- 对复数统计量并行输出所有合理标量解释，交给 fresh reviewer 证伪。
