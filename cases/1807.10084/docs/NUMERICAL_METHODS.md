# Numerical Methods

## 稳态主方程

以截断 Fock 基构造 `a`、`a†` 和 Kerr Hamiltonian。Liouvillian 按列向量化密度矩阵，使用一个迹约束替换奇异方程行，再求解复线性系统。输出前检查：

- `Tr(ρ)=1`；
- `ρ=ρ†`；
- 负本征值只允许数值舍入量级；
- `||Lρ||` 满足容差；
- 最高 Fock 态尾概率足够小。

## 参数与网格

- Fock cutoff：`12`；收敛复核：`10,12,14`
- 主要 `k` 网格：281–351 点；Supplement S7 为每个转速 241 点
- 转速：`0, 6.6, 15, 29, 30, 45, 58 kHz`
- 随机性：无；单模确定性稳态问题不需要 seed
- 总稳态点：6325

## 解析与语义目标

T001、T004、T006–T008 直接由论文公式生成；T015 从共振兼容条件逐行推导。T011 同时生成 Lindblad 数值值和弱驱动解析值，用于方法交叉验证。

## 输出与验证

- 21 个 CSV：`outputs/data/`
- 14 个独立科学图：`outputs/figures/`
- 15/15 target checks：`outputs/checks/target_checks.json`
- 收敛：`outputs/checks/convergence.json`
- 输出哈希：`outputs/checks/generated_data_manifest.json`
- 隔离证明：`outputs/runs/1807.10084-paper-exact-v2/run_attestation.json`

主要数值风险是 `g²/g³` 在极低平均光子数处对舍入敏感，以及分布尾部随 cutoff 变化。两者均由尾概率、残差和多 cutoff 对照约束。
