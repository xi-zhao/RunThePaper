# Lessons Learned

## Case Summary

- Paper：*Fixed-detector tilt--defocus sensing by upstream source coding in a time-reversed Young interferometer*
- PaperID：`2605.02873`
- Final status：5/5 科学目标通过，5/5 像素合约通过
- Main targets：FIG001A、FIG001B、FIG001C、FIG001D、FIGS001
- Main blockers：无；仅有作者数组缺失导致的科学评分证据上限，以及一处源图标签冲突

## What Worked

- 先把“有限宽 Fresnel 响应 → 局部分数 → 噪声度量编码 → Fisher 投影”整理成一个核心模型，再按目标切片输出，避免了五套互不一致的局部实现。
- 解析分数同时用中心差分验证，矩阵结果再用论文打印值验证，形成互相独立的两类证据。
- 生成路径与源图参考路径物理分离；像素工作开始前检查科学 JSON 全部通过。
- 使用主积分阶数加倍作为统一收敛检查，成本低且能覆盖全部目标。

## What Was Difficult

- Figure 1(d) 把多组矩阵、保留率与文字压在一个面板中，科学对象和像素对象需要分开表达。
- 原图面板的第二个 toy 保留率与 Supplement S4 不一致，若只追求像素文字会污染科学结果。
- Supplementary Figure S1 的大画布与主图面板裁切方式不同，需要独立注册，而不是复用主图布局。

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| 原图文本也可能是有误的参考资产 | 像素证据不能裁决物理真值 | 允许 `source_figure_artifact`，并要求公式/正文/独立数值三方证据 |
| 局部 Fisher 编码适合以“度量投影”作为核心模型 | 可同时解释正交性、归一化、信息保留和投影上界 | 优先测试不变量，再测试最终矩阵 |
| 像素注册必须按画布族分开 | 主图 panel crop 和补充整图有不同几何 | 为每个画布族声明独立 PixelLayoutTarget |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| 用原图曲线反推数据 | 原图可直接提供轮廓，但会破坏独立性 | 科学输出封存后才允许提取 source pixels |
| 把固定探测器和源坐标符号混淆 | Fresnel 相位对符号敏感 | 在 equation card 中逐项声明坐标与参数来源 |
| 用普通 \(L^2\) 正交替代噪声度量正交 | 会错误估计编码 Fisher 信息 | 将 \(N(y)\) 度量写成显式领域规则并测试 |
| 只看最终图形 | 可能掩盖导数符号或归一化错误 | 加有限差分、积分阶数加倍和投影上界检查 |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| 同一核心状态派生响应、分数、编码和 Fisher | 多个面板共享同一物理模型时 | 五个目标数值互相一致，全部门禁通过 |
| 独立导数检查 | 论文给出解析局部导数时 | FIG001B 误差低于 \(7.39\times10^{-10}\) |
| 以不变量校验压缩通道 | 构造最优测量/编码基时 | FIG001C 正交残差 \(2.22\times10^{-16}\) |
| 科学渲染与像素渲染分层 | 出版版式不等于科学数据结构时 | 科学分 90 与像素分 79.36 独立可审计 |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| source-text/science conflict | Figure 1(d) toy retention label | 对原图 OCR/文本、正文打印值和独立数值做三方一致性检查 |
| canvas-family registration mismatch | Supplementary Figure S1 初始像素合约 | 在评分前检查 source/generated 画布尺寸与轴框 IoU |
| cold font-cache timing contamination | 首次 FIG001A 渲染 | 记录 cold observation，接受计时使用同环境热缓存重跑 |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| 源图标签与正文数值冲突检查 | 防止像素目标覆盖科学真值 | Harness backlog candidate after Trial |
| 绘图 cold-cache 计时标记 | 避免把字体缓存算作模型成本 | Performance profiling helper |
| 科学生成脚本的 source-path 禁读声明 | 强化独立生成 provenance | Target runner contract |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Scope |
| --- | --- | --- |
| 向量化有限狭缝 Gauss–Legendre 积分 | 含 2× 阶数复算的五个接受运行总计 2.256 s | 保持 case-local |
| source chunking | 3001 源点与 512 积分点时内存稳定 | 可形成通用数值模式，但 Trial 内不推广 |
| 单一 response state | A–D 共享公式实现，不复制业务规则 | 保持 case-local |

## Harness Backlog Items

本轮是冻结 Trial，且用户明确禁止修改 protected Harness。上述候选仅记录在 case 内，未复制到 `private validation harness/HARNESS_BACKLOG.md`，也没有在本轮创建跨 case 变更。

| Priority | Improvement | Evidence | Status |
| --- | --- | --- | --- |
| medium | 增加 source-text/science conflict 的结构化审计字段 | FIG001D 原图与 Supplement S4 冲突 | deferred_by_frozen_trial |
| low | 将 cold-cache 与 accepted compute time 分栏 | FIG001A 首次字体缓存 | deferred_by_frozen_trial |

## Prompt Or Workflow Changes

- 像素工作开始前，除科学门禁外再封存生成数据哈希，可更直观证明后续注册没有修改科学数据。
- 遇到原图数值冲突时，应优先建立 `source_figure_artifact` 证据，而不是为了更高像素分修改生成值。
