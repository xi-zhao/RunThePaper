# Lessons Learned

## Case Summary

- Paper：Inverse Mpemba Effect Demonstrated on a Single Trapped Ion Qubit
- PaperID：`2401.05830`
- 当前状态：10/10 理论目标通过；5 个实验目标缺作者数据；fresh review 待完成
- 运行成本：本地 CPU 约 6 秒，无需 A100

## 可复用经验

| 经验 | 为什么重要 | 后续建议 |
| --- | --- | --- |
| 正文与补充材料必须逐项展开到同一规范 | 同一论文可能在 dissipator 归一化上差两倍，单看最终图发现不了 | 为每个独立公式来源生成可比较的规范化生成器 |
| 图像目标与实验数据目标分开建模 | 理论层可完整复现，但实验层缺计数，不能用理论曲线冒充 | figure coverage 允许同一主图拆 theory target 与 author-data blocker |
| 隔离运行要冻结字体缓存 | Matplotlib 首次启动会调用 fontconfig 子进程，造成与物理无关的证明失败 | 把确定版本的字体缓存列为运行输入并设置 `MPLCONFIGDIR` |
| 原图只能在数值冻结后进入 RenderContract | 既能做排版比较，又能证明数值未被像素反向污染 | 对照前后重算全部 CSV 哈希并写机器记录 |
| 第二数值通道要有不同实现结构 | Bloch 与密度矩阵两个实现能发现共同归一化错误 | 关键主张至少保留一个不同状态表示的交叉验证 |

## New Failure Modes

以下是本 case 新发现的失败模式。

| Failure mode | 本 case 的表现 | 自动检测建议 |
| --- | --- | --- |
| cross-section normalization drift | Main Eq. (1)-(2) 与 Supplement Eq. (1)-(4) 耗散率相差 2 | 对同一符号在正文/补充中的生成器做符号归一化 diff |
| first-run subprocess leakage | 初次隔离执行被 Matplotlib 字体缓存触发两次 subprocess | 在 runner 预检中验证字体缓存存在且 hash 已声明 |
| mixed experimental/theory panel ambiguity | Main Fig. 4 同时含实验点和理论线 | coverage 与评分必须声明只复现 theory numeric region |
| misleading pixel score | 不同坐标几何的整图差主要反映排版 | 无预声明同坐标 RenderContract 时强制 pixel N/A |

## Reusable Checks Or Tools

以下工具候选可以推广到后续 case。

| Candidate | 用途 | 去向 |
| --- | --- | --- |
| generator-normalization comparator | 检查正文/补充/附录对同一 GKSL 模型的系数一致性 | Harness formula audit |
| frozen matplotlib cache preflight | 消除隔离运行的字体子进程噪声 | isolated-run preflight |
| post-freeze data hash guard | RenderContract 前后证明数组未变 | generic render contract helper |

## Harness Backlog

| Priority | Improvement | Evidence | Status |
| --- | --- | --- | --- |
| P1 | 隔离 runner 增加 Matplotlib/fontconfig 预检 | v1 因 2 次字体子进程失败；v2 缓存冻结后 0 denied | proposed |
| P1 | 公式卡增加跨章节规范化一致性门 | factor-two discrepancy 对所有温度轴有系统影响 | proposed |
| P2 | 混合实验/理论面板支持显式 layer scope | Main Fig. 4 理论层通过、实验层缺数据 | proposed |
