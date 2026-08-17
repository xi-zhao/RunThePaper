# Lessons Learned

## Case Summary

- PaperID：`0911.0556`。
- 完成：10 个数值子图、1 个定量文本声明，19/19 科学断言通过。
- 主要边界：Fig. 3 缺两个原始参数；fresh-context review 未完成。

## 可复用经验

| 经验 | 为什么重要 | 后续做法 |
| --- | --- | --- |
| 随机事件图应比较统计量与科学区域，不要求逐事件重合 | 独立随机实现不应复制作者随机样本 | 固定 seed 只保证本 case 可重复，并检查 activity/window |
| birth–death 生成元可先做对称相似变换 | 提高大 cutoff 本征求解稳定性 | 同时保留直接非对称求解作独立交叉检查 |
| 论文漏参数不是算力不足 | 加大计算不会补出参数身份 | 明确 direct/root cause，代码照常写完并执行 |
| 后续同作者参数只能支持 reconstructed feature | 避免把合理猜测冒充 paper-exact | provenance 中分开 original 与 later-public source |
| 像素高分可能主要来自白背景 | 像素不能替代物理 | 像素为主展示指标，公式/物理/参数/隔离证据 fail-closed 封顶 |
| 图注符号疑点需要 fresh review | 复现会话容易自证 | 只记录 discrepancy，不在当前上下文确认 paper error |

## New Failure Modes

| Failure mode | 本 case 表现 | 自动检测建议 |
| --- | --- | --- |
| 后续文献参数被误当原文参数 | Fig. 3 可算但不是 paper-exact | provenance 必须记录 source revision 与 target-level parameter status |
| 全区像素分被白背景抬高 | 全区 91–97，但前景分更低 | 同时报 foreground metric，不允许其替代物理检查 |
| 同一图中 bias 标签重复 | Fig. 3(D) 两条不同曲线都写 `s=-0.05` | fresh review 检查标签与相序的一致性 |

## Reusable Checks Or Tools

| Candidate | 用途 | 建议位置 |
| --- | --- | --- |
| 对称 birth–death eigensolver + 直接 solver parity | 排除三对角非厄米求解错误 | 先留 case-local，第二个 case 再抽象 |
| event-raster activity/window validator | 随机事件图的科学验收 | 可提炼进 Harness |
| frozen-data RenderContract hash guard | 确认排版优化不改数值 | 已由 case test 覆盖 |

## Harness backlog

| Priority | 改进 | 证据 | 状态 |
| --- | --- | --- | --- |
| P1 | 为 `reconstructed_from_later_publication` 增加明确 parameter enum，替代宽泛 `unknown` | T008–T010 当前被 `unknown` 表达 | case-local lesson |
| P2 | 像素报告同时展示 foreground score，减少白背景均值误读 | T010 全区 96.52、前景 45.77 | case-local lesson |
| P2 | 对随机 event raster 提供事件率/间隔分布专用视觉 metric | T003 全区像素仅 81.77，但统计物理通过 | case-local lesson |

本次只修改 case，不直接改全局 Harness backlog。
