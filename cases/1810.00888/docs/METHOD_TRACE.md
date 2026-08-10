# Method trace

| 方法 | 责任 | 独立性 |
|---|---|---|
| NUM_EXACT | 约束基、PXP Hamiltonian、对称扇区、精确对角化 | 只依赖论文公式和公开参数 |
| NUM_MPS | Gamma、Xi、Upsilon 的张量收缩 | 未读取作者代码或数组 |
| NUM_EVIDENCE | 谱塔选择、简并子空间不变量、标注值和 protocol-v2 检查 | 与绘图分离 |
| RENDER001 | 冻结数据之后的画幅、字体、配色和线型 | 哈希锁定，不能改物理数组 |

数值生成与渲染是两个单向阶段：numerics -> frozen data -> RenderContract -> pixel evidence。
