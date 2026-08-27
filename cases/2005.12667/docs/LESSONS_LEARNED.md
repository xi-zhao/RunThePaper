# Lessons Learned

## Case Summary

- Paper: *Circuit Quantum Electrodynamics*
- PaperID: 2005.12667
- Final status: numerical_feature_reproduction, score 90
- Main targets: Sec. III Eqs. 29--63, Figs. 8--9, Sec. IV Eqs. 66--68 and 70--75
- Main blockers: none in scope；source schematics omit absolute plotting parameters

## What Worked

- 把公式卡 gate 放在数值代码之前，迫使每个近似、分母和符号都有来源和极限检查。
- 用正式发表版交叉校勘预印本，发现式 (29)、(51)、(67) 三处会改变可执行物理的修订。
- 用物理不变量而非图像像素判断：谱下有界、Hamiltonian 厄米、Lindblad 保迹/正、无损端口 \(|r|=1\)。
- 图 9 用裸态重叠 assignment，避免能级排序在混合后产生假匹配。

## What Was Difficult

- 论文是大型综述，用户只选第三章和第四章部分公式；需要既完整分类全篇图，又避免把范围外工作包装成阻塞。
- 端口场的单个符号可以被相位重定义，但边界式和 Langevin 驱动项的相对符号决定能流守恒，必须区分“约定”与“物理”。
- 解析能级图没有绝对绘图参数，不能用视觉相似替代参数映射。

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| 预印本与正式版必须在公式 gate 前交叉比对 | 正式版可能修掉会让代码非厄米或系数错误的 typo | 建立 source-correction ledger，双锚点记录公式 |
| 守恒量/正性/被动性是高价值 oracle | 不需要作者数据即可捕获符号与因子错误 | 每种物理模型至少声明一个不可妥协 invariant |
| 公式图缺参数时应做 analytic-reference feature reproduction | 防止把代表性参数误报为 paper-exact | scorecard 标记 parameter_match=not_applicable 与 exploratory |
| 状态追踪应依赖本征态身份而非能量序 | 避免 avoided crossing 附近误配 | 默认使用 overlap-based assignment |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| 只信用户给的 PDF 版本 | arXiv Eqs. 29/51/67 含已修订问题 | 自动检查 DOI/正式版并生成公式 diff 候选 |
| 把相位约定当作任意相对符号 | Eqs. 72/75 同号组合破坏 passivity | 对散射问题强制 unitarity/flux check |
| 按本征值排序匹配裸态 | 色散能级可能重排 | 保存 overlap 和 assignment evidence |
| 用源图像作为“数值证据” | 图 8/9 仅是示意 | 只用 independent numerics 或 analytic reference 评分 |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| cross-version formula audit | 有 arXiv 与正式出版版本 | 捕获 3 个实质修订 |
| formula-first gate | 公式驱动论文 | 15/15 cards open before final execution |
| invariant suite | 缺作者原始数组 | 10 unit tests + chapter/open checks |
| explicit reconstruction label | 来源约定不完备 | EQ075 保持 `reconstructed` 而非伪称 verified source form |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| preprint equation corrected only in formal publication | Eqs. 29, 51, 67 | cross-version equation/source diff + invariant checks |
| individually plausible sign conventions become inconsistent when composed | Eqs. 72 and 75 | end-to-end power/flux conservation check |
| coefficient passes dimensional analysis but fails combinatorics | Eq. 51 extra factor 1/2 | expand operator polynomial and compare Hamiltonian conventions |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| preprint/formal equation correction ledger | 所有版本化论文适用 | harness formula workflow |
| Hermiticity residual checker | 捕获缺少 \(i\)/错误相对号 | generic formula invariant library |
| one-port passivity checker | 输入输出/散射论文通用 | generic physics checks |
| overlap-based eigenstate matcher | 多能级与 avoided crossings 通用 | numerical helper |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Boundary |
| --- | --- | --- |
| JC invariant-block diagonalization | exact 2x2 blocks, negligible runtime | promote pattern, not paper constants |
| 40D dense Duffing solve + Hungarian match | stable identity labels, full case <1.2 s | matcher potentially generic |
| 16-level dense Lindblad ODE | analytic agreement \(5\times10^{-11}\) | case-local scale |

## Harness Backlog Items

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| P1 | add cross-version equation correction ledger/check | three corrected formulas | copied_to_backlog |
| P2 | add reusable physical-invariant declarations to formula cards | Hermiticity/passivity caught source issues | copied_to_backlog |

## Prompt Or Workflow Changes

- 在公式驱动复现中，先问“正式版是否改过这条式子”，再把 PDF 公式转成代码。
- 对端口、规范、Fourier 约定，要求至少一个 convention-independent observable 闭合整个推导。
- 本案例的抽象经验已写入 `PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`，具体工具需求已写入 `PRAgent-workflow/HARNESS_BACKLOG.md`。
