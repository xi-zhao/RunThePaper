# Lessons Learned

## Case Summary

- Paper：*Nonreciprocal Photon Blockade*
- Paper ID：`1807.10084`
- 科学状态：15/15 目标检查通过，完整运行约 9 秒
- 主阻塞：其余连续数值图的 RenderContract；fresh-context 独立评审

## 可复用经验

| 经验 | 为什么重要 | 后续做法 |
| --- | --- | --- |
| 先统一方向符号再写 solver | Fizeau 正负号决定全部 PB/PIT 结论 | 在公式卡中固定传播方向、旋转方向和 `Δ_F` 符号 |
| 理想能级比值与打印转速分离 | `58/29 kHz` 是舍入值，不能替代 `f=1/1/2` | 数据模型分别保存 schematic 与 physical 参数 |
| 每个 Supplement 子图都入 ledger | S3 实际包含 8 对、16 个方向图，粗粒度 target 容易漏图 | 先枚举 panel，再允许执行 |
| 隔离 runner 要冻结字体缓存 | Matplotlib 首次字体发现会启动子进程，破坏审计 | 将字体缓存作为显式输入，禁用运行期发现 |
| 科学数组与渲染优化分通道 | 否则像素优化可能污染物理参数 | runner 冻结 CSV+哈希；RenderContract 仅改样式 |
| 主像素区与整图诊断分开 | 标题、字体、留白会掩盖科学曲线质量 | 主分只算预声明理论区，整图分只诊断排版 |
| 小模型不占用 A100 | 本例全量只需约 9 秒 | A100 留给训练、大规模 ED/MPS、随机采样等重任务 |

## New Failure Modes

1. 被标记为 `blocked_prerequisite_gate` 的像素 target 仍会被 crop builder 处理。已修正为只有 `declared`、`ready_for_pixel_evidence`、`pixel_compared` 才生成像素证据。
2. “目标必须完成”与“目标必须进入一个标量均值”曾被绑在一起。已增加 `score_aggregation=excluded`：目标仍是 critical，仍受科学、执行、像素和评审门禁约束，但无同类主指标时不污染均值。
3. 对未注册的自由重绘图计算全图 SSIM 会产生看似精确、实则无意义的数字。当前只保留并排诊断；正式 diff 仅对 RenderContract 后的 T006 生成。

## Reusable Checks Or Tools

| 工具/检查 | 可复用价值 | 落点 |
| --- | --- | --- |
| pixel crop readiness gate | 阻止 blocked target 提前进入像素证据 | `rr_harness/pixel_layout.py` |
| isolated font-cache bundle | 避免 Matplotlib 隐式子进程破坏独立运行证明 | run attestation contract |
| scientific-region/full-layout split | 让主分测科学区，整图只诊断排版 | PixelLayoutTarget + scorecard |
| frozen-data RenderContract | 允许看原图调样式，同时证明物理数组未变 | case-local renderer contract |

## 推荐工作流

`全文理解 → 公式卡 → 全数值 panel ledger → 隔离数值运行 → 数据哈希 → 科学检查 → RenderContract → 科学区像素证据 → fresh-context 证伪评审 → authoritative state`
